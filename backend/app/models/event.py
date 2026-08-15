"""Event model — a recorded AI detection / violation"""
from sqlalchemy import String, Integer, ForeignKey, DateTime, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.camera import Camera


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    camera_id: Mapped[int] = mapped_column(ForeignKey("cameras.id"), index=True)
    module_name: Mapped[str] = mapped_column(String(50), index=True)            # 'helmet','fire',...
    message: Mapped[str] = mapped_column(String(200))
    confidence: Mapped[float] = mapped_column(Float)
    snapshot_path: Mapped[str] = mapped_column(String(300), default="")
    video_clip_path: Mapped[str] = mapped_column(String(300), default="")
    critical: Mapped[bool] = mapped_column(Boolean, default=False)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    acknowledged_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    camera: Mapped["Camera"] = relationship(back_populates="events")
