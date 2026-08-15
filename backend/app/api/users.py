"""User management - admin-only CRUD"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime

from app.core.database import get_db
from app.core.security import hash_password
from app.core.auth import get_current_user, require_admin
from app.core.email import send_welcome_email
from app.models.user import User

router = APIRouter()


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    active: bool
    pending: bool = False
    requested_role: str = "operator"
    request_reason: str = ""
    last_seen: Optional[datetime] = None
    department_filter: str = ""
    avatar_url: str = ""

    class Config:
        from_attributes = True


class UserCreateIn(BaseModel):
    email: EmailStr
    full_name: str
    role: str = "operator"
    password: Optional[str] = None
    department_filter: str = ""


class UserUpdateIn(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    active: Optional[bool] = None
    department_filter: Optional[str] = None
    password: Optional[str] = None


@router.get("", response_model=List[UserOut])
async def list_users(db: AsyncSession = Depends(get_db), current: User = Depends(get_current_user)):
    if current.role == "admin":
        res = await db.execute(select(User).order_by(User.pending.desc(), User.id))
        return res.scalars().all()
    return [current]


@router.get("/pending", response_model=List[UserOut])
async def list_pending(db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    res = await db.execute(select(User).where(User.pending == True).order_by(User.id.desc()))
    return res.scalars().all()


@router.post("/{user_id}/approve", response_model=UserOut)
async def approve_user(user_id: int, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    u = await db.get(User, user_id)
    if not u:
        raise HTTPException(404, "Foydalanuvchi topilmadi")
    if not u.pending:
        raise HTTPException(400, "Bu foydalanuvchi allaqachon tasdiqlangan")
    from secrets import token_urlsafe
    from app.core.security import hash_password
    new_password = token_urlsafe(8)
    u.password_hash = hash_password(new_password)
    u.pending = False
    u.active = True
    await db.commit()
    await db.refresh(u)
    try:
        from app.core.email import send_approval_email
        send_approval_email(u.email, u.full_name, u.role, new_password)
    except Exception as e:
        print("[Users] approval email failed:", e)
    return u


@router.post("/{user_id}/reject", status_code=204)
async def reject_user(user_id: int, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    u = await db.get(User, user_id)
    if not u:
        raise HTTPException(404, "Foydalanuvchi topilmadi")
    if not u.pending:
        raise HTTPException(400, "Faqat kutilayotgan so'rovlarni rad etish mumkin")
    email = u.email
    full_name = u.full_name
    await db.delete(u)
    await db.commit()
    try:
        from app.core.email import send_rejection_email
        send_rejection_email(email, full_name)
    except Exception as e:
        print("[Users] rejection email failed:", e)


@router.post("", response_model=UserOut, status_code=201)
async def create_user(data: UserCreateIn, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    if data.role not in {"admin", "manager", "operator", "auditor"}:
        raise HTTPException(400, "Notogri rol")
    existing = await db.execute(select(User).where(User.email == data.email.lower()))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Bu email allaqachon ishlatilgan")
    username = data.email.split("@")[0].lower()
    base_username = username
    suffix = 1
    while True:
        check = await db.execute(select(User).where(User.username == username))
        if not check.scalar_one_or_none():
            break
        suffix += 1
        username = base_username + str(suffix)
    password = data.password or "changeme123"
    u = User(
        username=username, email=data.email.lower(), full_name=data.full_name,
        role=data.role, password_hash=hash_password(password),
        department_filter=data.department_filter, active=True,
    )
    db.add(u)
    await db.commit()
    await db.refresh(u)
    try:
        send_welcome_email(u.email, u.full_name, u.role, admin.full_name or admin.username)
    except Exception as e:
        print("[Users] welcome email failed:", e)
    return u


@router.put("/{user_id}", response_model=UserOut)
async def update_user(user_id: int, data: UserUpdateIn, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    u = await db.get(User, user_id)
    if not u:
        raise HTTPException(404, "Foydalanuvchi topilmadi")
    if data.full_name is not None:
        u.full_name = data.full_name
    if data.role is not None:
        if data.role not in {"admin", "manager", "operator", "auditor"}:
            raise HTTPException(400, "Notogri rol")
        u.role = data.role
    if data.active is not None:
        u.active = data.active
    if data.department_filter is not None:
        u.department_filter = data.department_filter
    if data.password:
        u.password_hash = hash_password(data.password)
    await db.commit()
    await db.refresh(u)
    return u


@router.post("/{user_id}/toggle-lock")
async def toggle_lock(user_id: int, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    u = await db.get(User, user_id)
    if not u:
        raise HTTPException(404, "Foydalanuvchi topilmadi")
    if u.id == admin.id:
        raise HTTPException(400, "Ozingizni bloklay olmaysiz")
    u.active = not u.active
    await db.commit()
    return {"ok": True, "active": u.active}


@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    u = await db.get(User, user_id)
    if not u:
        raise HTTPException(404, "Foydalanuvchi topilmadi")
    if u.id == admin.id:
        raise HTTPException(400, "Ozingizni ochira olmaysiz")
    await db.delete(u)
    await db.commit()
