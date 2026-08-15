"""Camera model — physical CCTV with RTSP + AI modules"""
from sqlalchemy import String, Integer, Boolean, ForeignKey, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, TYPE_CHECKING

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.event import Event


class Camera(Base):
    __tablename__ = "cameras"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    location: Mapped[str] = mapped_column(String(200), default="")
    rtsp_url: Mapped[str] = mapped_column(String(300))
    ip: Mapped[str] = mapped_column(String(50), default="")
    mac: Mapped[str] = mapped_column(String(20), default="")
    onvif_user: Mapped[str] = mapped_column(String(80), default="")
    onvif_pass_enc: Mapped[str] = mapped_column(String(200), default="")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    online: Mapped[bool] = mapped_column(Boolean, default=False)
    fps_actual: Mapped[float] = mapped_column(Float, default=0.0)

    # AI per-camera config
    modules_enabled: Mapped[list] = mapped_column(JSON, default=list)          # ['helmet','fire','zone']
    confidence_threshold: Mapped[float] = mapped_column(Float, default=0.65)
    cooldown_sec: Mapped[int] = mapped_column(Integer, default=60)
    polygons: Mapped[list] = mapped_column(JSON, default=list)                 # restricted zones

    # Relations
    department_id: Mapped[Optional[int]] = mapped_column(ForeignKey("departments.id"))
    department: Mapped[Optional["Department"]] = relationship(back_populates="cameras")
    events: Mapped[List["Event"]] = relationship(back_populates="camera", cascade="all, delete-orphan")
