"""Authentication endpoints - email OTP + password + Google + JWT"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.core.otp import otp_store
from app.core.email import send_otp_email
from app.core.auth import get_current_user
from app.api.auth_google import google_login_handler, GoogleLoginIn
from app.models.user import User

router = APIRouter()


class RequestCodeIn(BaseModel):
    email: EmailStr


class VerifyCodeIn(BaseModel):
    email: EmailStr
    code: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class RegisterRequestIn(BaseModel):
    email: EmailStr
    full_name: str
    requested_role: str = "operator"
    reason: str = ""


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class MeOut(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    active: bool
    avatar_url: str = ""

    class Config:
        from_attributes = True


class UpdateMeIn(BaseModel):
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    password: Optional[str] = None


def user_dict(u: User) -> dict:
    return {"id": u.id, "username": u.username, "email": u.email,
            "full_name": u.full_name, "role": u.role,
            "avatar_url": getattr(u, "avatar_url", "") or ""}


@router.get("/config")
async def get_auth_config():
    return {
        "google_client_id": settings.GOOGLE_CLIENT_ID or None,
        "smtp_configured": bool(settings.SMTP_HOST and settings.SMTP_USER),
        "demo_mode": not bool(settings.SMTP_HOST and settings.SMTP_USER),
    }


@router.post("/request-code")
async def request_code(data: RequestCodeIn, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(User).where(User.email == data.email.lower()))
    user = res.scalar_one_or_none()
    if not user:
        return {"ok": True, "message": "Agar email mavjud bolsa kod yuborildi"}
    if not user.active:
        raise HTTPException(status_code=403, detail="Hisob bloklangan")
    code = otp_store.generate(data.email.lower())
    sent = send_otp_email(data.email, code)
    response = {
        "ok": True,
        "message": "Kod yuborildi" if sent else "Kod yaratildi (demo)",
        "expires_in_seconds": 600,
        "demo_mode": not sent,
    }
    if not sent and settings.DEBUG:
        response["demo_code"] = code
    return response


@router.post("/verify-code", response_model=TokenOut)
async def verify_code(data: VerifyCodeIn, db: AsyncSession = Depends(get_db)):
    if not otp_store.verify(data.email.lower(), data.code):
        raise HTTPException(status_code=400, detail="Notogri yoki muddati otgan kod")
    res = await db.execute(select(User).where(User.email == data.email.lower()))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=403, detail="Hisob mavjud emas")
    if user.pending:
        raise HTTPException(status_code=403, detail="Sorovingiz hali tasdiqlanmagan, adminni kuting")
    if not user.active:
        raise HTTPException(status_code=403, detail="Hisob bloklangan")
    user.last_seen = datetime.utcnow()
    await db.commit()
    await db.refresh(user)
    return TokenOut(access_token=create_access_token(user.id, user.email, user.role), user=user_dict(user))


@router.post("/login", response_model=TokenOut)
async def login(data: LoginIn, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(User).where(User.email == data.email.lower()))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Email yoki parol notogri")
    if user.pending:
        raise HTTPException(status_code=403, detail="Sorovingiz hali tasdiqlanmagan, adminni kuting")
    if not user.active:
        raise HTTPException(status_code=401, detail="Hisob bloklangan")
    if not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email yoki parol notogri")
    user.last_seen = datetime.utcnow()
    await db.commit()
    await db.refresh(user)
    return TokenOut(access_token=create_access_token(user.id, user.email, user.role), user=user_dict(user))


@router.post("/google", response_model=TokenOut)
async def google_login(data: GoogleLoginIn, db: AsyncSession = Depends(get_db)):
    return await google_login_handler(data, db)


@router.post("/register-request")
async def register_request(data: RegisterRequestIn, db: AsyncSession = Depends(get_db)):
    """Public endpoint: anyone can request to join. Admin reviews."""
    if data.requested_role not in {"manager", "operator", "auditor"}:
        raise HTTPException(400, "Notogri rol")
    res = await db.execute(select(User).where(User.email == data.email.lower()))
    existing = res.scalar_one_or_none()
    if existing:
        if existing.pending:
            return {"ok": True, "message": "Sorovingiz allaqachon yuborilgan, admin javobini kuting"}
        raise HTTPException(400, "Bu email allaqachon roy'xatdan otgan")
    from secrets import token_urlsafe
    from app.core.security import hash_password
    username = data.email.split("@")[0].lower()
    base = username
    suffix = 1
    while True:
        check = await db.execute(select(User).where(User.username == username))
        if not check.scalar_one_or_none():
            break
        suffix += 1
        username = base + str(suffix)
    u = User(
        username=username, email=data.email.lower(), full_name=data.full_name,
        role=data.requested_role, requested_role=data.requested_role,
        password_hash=hash_password(token_urlsafe(16)),
        request_reason=data.reason, pending=True, active=False,
    )
    db.add(u)
    await db.commit()
    return {"ok": True, "message": "Sorovingiz adminga yuborildi. Tasdiqlashni kuting."}


@router.get("/me", response_model=MeOut)
async def me(user: User = Depends(get_current_user)):
    return user


@router.put("/me", response_model=MeOut)
async def update_me(data: UpdateMeIn, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    from app.core.security import hash_password
    if data.full_name is not None:
        name = data.full_name.strip()
        if not name or len(name) < 2:
            raise HTTPException(400, "Ism kamida 2 belgi bo'lishi kerak")
        user.full_name = name
    if data.avatar_url is not None:
        user.avatar_url = data.avatar_url[:500]
    if data.password:
        if len(data.password) < 6:
            raise HTTPException(400, "Parol kamida 6 belgi bo'lishi kerak")
        user.password_hash = hash_password(data.password)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/logout")
async def logout(user: User = Depends(get_current_user)):
    return {"ok": True, "message": "Tizimdan chiqildi"}
