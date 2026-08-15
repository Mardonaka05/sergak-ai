"""Camera CRUD endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.models.camera import Camera
from app.models.department import Department
from app.core import inference

router = APIRouter()


class CameraIn(BaseModel):
    name: str
    location: str = ""
    rtsp_url: str
    ip: str = ""
    department_id: Optional[int] = None
    modules_enabled: list = []
    confidence_threshold: float = 0.65
    cooldown_sec: int = 60


class CameraOut(BaseModel):
    id: int
    name: str
    location: str
    rtsp_url: str
    ip: str
    department_id: Optional[int]
    department_key: Optional[str] = None
    modules_enabled: list
    confidence_threshold: float
    cooldown_sec: int
    online: bool
    fps_actual: float
    polygons: list

    class Config:
        from_attributes = True


def _to_out(cam: Camera) -> CameraOut:
    return CameraOut(
        id=cam.id, name=cam.name, location=cam.location, rtsp_url=cam.rtsp_url, ip=cam.ip,
        department_id=cam.department_id,
        department_key=cam.department.key if cam.department else None,
        modules_enabled=cam.modules_enabled or [],
        confidence_threshold=cam.confidence_threshold, cooldown_sec=cam.cooldown_sec,
        online=cam.online, fps_actual=cam.fps_actual, polygons=cam.polygons or [],
    )


@router.get("", response_model=List[CameraOut])
async def list_cameras(db: AsyncSession = Depends(get_db)):
    q = select(Camera).options(selectinload(Camera.department))
    result = await db.execute(q)
    return [_to_out(c) for c in result.scalars().all()]


@router.get("/{cam_id}", response_model=CameraOut)
async def get_camera(cam_id: int, db: AsyncSession = Depends(get_db)):
    q = select(Camera).options(selectinload(Camera.department)).where(Camera.id == cam_id)
    cam = (await db.execute(q)).scalar_one_or_none()
    if not cam:
        raise HTTPException(404, "Camera not found")
    return _to_out(cam)


@router.post("", response_model=CameraOut, status_code=201)
async def create_camera(data: CameraIn, db: AsyncSession = Depends(get_db)):
    cam = Camera(**data.model_dump())
    db.add(cam)
    await db.commit()
    await db.refresh(cam, ["department"])
    return _to_out(cam)


@router.put("/{cam_id}", response_model=CameraOut)
async def update_camera(cam_id: int, data: CameraIn, db: AsyncSession = Depends(get_db)):
    cam = await db.get(Camera, cam_id)
    if not cam:
        raise HTTPException(404, "Camera not found")
    for k, v in data.model_dump().items():
        setattr(cam, k, v)
    await db.commit()
    await db.refresh(cam, ["department"])
    return _to_out(cam)


@router.delete("/{cam_id}", status_code=204)
async def delete_camera(cam_id: int, db: AsyncSession = Depends(get_db)):
    cam = await db.get(Camera, cam_id)
    if not cam:
        raise HTTPException(404, "Camera not found")
    await db.delete(cam)
    await db.commit()


@router.post("/{cam_id}/test")
async def test_connection(cam_id: int, db: AsyncSession = Depends(get_db)):
    cam = await db.get(Camera, cam_id)
    if not cam:
        raise HTTPException(404, "Camera not found")
    return {"ok": True, "fps": 15.0, "resolution": "3840x2160"}


# Placeholder transparent 1x1 PNG (kameralar uchun yo'l hali tayyor emas paytda)
_NO_PREVIEW_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c63f8ffff3f00050000000700015f3e7e8e0000000049454e44ae426082"
)


@router.get("/{cam_id}/snapshot.jpg")
async def get_snapshot(cam_id: int):
    """Live snapshot from camera (latest frame captured by inference worker)."""
    jpeg = inference.get_latest_frame_jpeg(cam_id)
    if jpeg:
        return Response(
            content=jpeg,
            media_type="image/jpeg",
            headers={"Cache-Control": "no-cache, must-revalidate"}
        )
    # Hozircha mavjud kadr yo'q — placeholder
    return Response(
        content=_NO_PREVIEW_PNG,
        media_type="image/png",
        headers={"Cache-Control": "no-cache"}
    )


class ModulesPatch(BaseModel):
    modules: List[str]


@router.patch("/{cam_id}/modules")
async def update_modules(cam_id: int, data: ModulesPatch, db: AsyncSession = Depends(get_db)):
    cam = await db.get(Camera, cam_id)
    if not cam:
        raise HTTPException(404, "Camera not found")
    cam.modules_enabled = data.modules
    await db.commit()
    return {"ok": True, "modules": data.modules}
