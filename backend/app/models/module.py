"""Module model — AI detection module (helmet, fire, etc.)"""
from sqlalchemy import String, Integer, Boolean, Float, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from app.core.database import Base


class Module(Base):
    __tablename__ = "modules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(50), unique=True, index=True)       # 'helmet'
    name: Mapped[str] = mapped_column(String(100))                              # 'Kaska Aniqlash'
    description: Mapped[str] = mapped_column(String(500), default="")
    model_path: Mapped[str] = mapped_column(String(300), default="")            # path to .pt or .engine
    model_filename: Mapped[str] = mapped_column(String(200), default="")        # original filename
    model_version: Mapped[str] = mapped_column(String(30), default="v1")
    architecture: Mapped[str] = mapped_column(String(40), default="")           # YOLOv8n/s/m/l
    file_size_mb: Mapped[float] = mapped_column(Float, default=0.0)
    class_names: Mapped[str] = mapped_column(Text, default="[]")                # JSON: ["helmet","head"]
    num_classes: Mapped[int] = mapped_column(Integer, default=0)
    confidence_threshold: Mapped[float] = mapped_column(Float, default=0.65)
    cooldown_sec: Mapped[int] = mapped_column(Integer, default=60)
    priority: Mapped[str] = mapped_column(String(20), default="normal")         # critical/high/normal/low
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    icon: Mapped[str] = mapped_column(String(50), default="boxes")
    color: Mapped[str] = mapped_column(String(20), default="#3b82f6")
    image_url: Mapped[str] = mapped_column(String(500), default="")             # cover image
    is_custom: Mapped[bool] = mapped_column(Boolean, default=False)             # user-uploaded vs built-in
    total_detections: Mapped[int] = mapped_column(Integer, default=0)
    avg_inference_ms: Mapped[float] = mapped_column(Float, default=0.0)
    accuracy_pct: Mapped[float] = mapped_column(Float, default=0.0)             # latest reported accuracy
    last_used_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
