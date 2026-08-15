"""Department model — groups cameras by physical area (Eritish, Pechkaxona, etc.)"""
from sqlalchemy import String, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, TYPE_CHECKING

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.camera import Camera


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(50), unique=True, index=True)      # 'eritish', 'pechka'
    name: Mapped[str] = mapped_column(String(100))                             # 'Eritish bo'limi'
    color: Mapped[str] = mapped_column(String(20), default="#3b82f6")
    icon: Mapped[str] = mapped_column(String(50), default="building-2")
    rules: Mapped[dict] = mapped_column(JSON, default=dict)                    # per-dept module rules

    cameras: Mapped[List["Camera"]] = relationship(back_populates="department")
