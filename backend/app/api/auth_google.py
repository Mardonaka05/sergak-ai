"""Google Sign-In handler - kept in separate file to avoid file size issues"""
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from datetime import datetime
import secrets

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.models.user import User


class GoogleLoginIn(BaseModel):
    credential: str


async def google_login_handler(data: GoogleLoginIn, db: AsyncSession):
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=503,
            detail="Google login sozlanmagan. Admin .env faylida GOOGLE_CLIENT_ID ni ornatishi kerak.",
        )
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests
        info = id_token.verify_oauth2_token(
            data.credential, google_requests.Request(), settings.GOOGLE_CLIENT_ID
        )
    except ImportError:
        raise HTTPException(status_code=503, detail="google-auth ornatilmagan")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Google token notogri: {e}")

    email = (info.get("email") or "").lower()
    if not email or not info.get("email_verified"):
        raise HTTPException(status_code=401, detail="Google email tasdiqlanmagan")

    name = info.get("name") or email
    res = await db.execute(select(User).where(User.email == email))
    user = res.scalar_one_or_none()

    if not user:
        cnt = (await db.execute(select(func.count(User.id)))).scalar() or 0
        if cnt == 0:
            user = User(
                username=email.split("@")[0].lower(),
                email=email, full_name=name, role="admin",
                password_hash=hash_password(secrets.token_urlsafe(16)),
                active=True, last_seen=datetime.utcnow(),
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        else:
            # Create as pending user — admin must approve
            base_username = email.split("@")[0].lower()
            username = base_username
            suffix = 1
            while True:
                check = await db.execute(select(User).where(User.username == username))
                if not check.scalar_one_or_none():
                    break
                suffix += 1
                username = base_username + str(suffix)
            new_pending = User(
                username=username, email=email, full_name=name,
                role="operator", requested_role="operator",
                password_hash=hash_password(secrets.token_urlsafe(16)),
                request_reason="Google orqali ro'yxatdan o'tish so'rovi",
                pending=True, active=False,
            )
            db.add(new_pending)
            await db.commit()
            raise HTTPException(
                status_code=403,
                detail="So'rovingiz adminga yuborildi. Admin tasdiqlashini kuting.",
            )

    if user.pending:
        raise HTTPException(status_code=403, detail="Sorovingiz hali tasdiqlanmagan, adminni kuting")
    if not user.active:
        raise HTTPException(status_code=403, detail="Hisob bloklangan")

    user.last_seen = datetime.utcnow()
    await db.commit()
    await db.refresh(user)

    from app.api.auth import TokenOut, user_dict
    return TokenOut(
        access_token=create_access_token(user.id, user.email, user.role),
        user=user_dict(user),
    )
