"""User model — RBAC (admin/manager/operator/auditor)"""
from sqlalchemy import String, Integer, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Optional

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(150), default="")
    role: Mapped[str] = mapped_column(String(20), default="operator")           # admin/manager/operator/auditor
    department_filter: Mapped[str] = mapped_column(String(200), default="")     # which depts this user can see
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    pending: Mapped[bool] = mapped_column(Boolean, default=False)
    requested_role: Mapped[str] = mapped_column(String(20), default="operator")
    request_reason: Mapped[str] = mapped_column(String(500), default="")
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    avatar_url: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
