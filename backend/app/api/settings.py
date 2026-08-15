"""System settings — read current, update some keys"""
from fastapi import APIRouter
from pydantic import BaseModel
from app.core.config import settings

router = APIRouter()


class SystemInfo(BaseModel):
    version: str = "2.1.4"
    hardware: str = "NVIDIA Jetson Orin NX 16GB"
    python: str = "3.10.12"
    inference_mode: str
    frame_skip: int
    motion_triggered: bool


@router.get("/system", response_model=SystemInfo)
async def get_system_info():
    return SystemInfo(
        inference_mode=settings.INFERENCE_MODE,
        frame_skip=settings.FRAME_SKIP,
        motion_triggered=settings.MOTION_TRIGGERED,
    )


class AIConfigIn(BaseModel):
    inference_mode: str | None = None
    frame_skip: int | None = None
    motion_triggered: bool | None = None
    default_confidence: float | None = None


@router.patch("/ai")
async def update_ai_config(data: AIConfigIn):
    if data.inference_mode: settings.INFERENCE_MODE = data.inference_mode
    if data.frame_skip is not None: settings.FRAME_SKIP = data.frame_skip
    if data.motion_triggered is not None: settings.MOTION_TRIGGERED = data.motion_triggered
    if data.default_confidence is not None: settings.DEFAULT_CONFIDENCE = data.default_confidence
    return {"ok": True}
