"""AI modules — full CRUD with .pt validation, image upload, replace, delete.

Designed so admins can fully manage AI models from the dashboard:
  - Upload .pt files (auto-extract architecture + class names if ultralytics is available)
  - Upload preview images
  - Edit confidence/cooldown/priority/icon/color/description
  - Toggle enabled/disabled
  - Replace existing .pt with a new version
  - Delete (both DB row + files on disk)
"""
import json
import os
import re
import shutil
import uuid as uuid_lib
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from app.core.database import get_db
from app.core.config import settings
from app.core.auth import get_current_user, require_admin
from app.models.module import Module
from app.models.user import User

router = APIRouter()

# Optional ultralytics import — if present we can validate .pt files
try:
    import torch  # noqa
    HAS_TORCH = True
except Exception:
    HAS_TORCH = False

try:
    from ultralytics import YOLO  # noqa
    HAS_ULTRALYTICS = True
except Exception:
    HAS_ULTRALYTICS = False

MODELS_DIR = settings.MODELS_DIR
MODELS_DIR.mkdir(parents=True, exist_ok=True)
MODULE_IMG_DIR = settings.BASE_DIR / "module_images"
MODULE_IMG_DIR.mkdir(parents=True, exist_ok=True)


# ============ Schemas ============

class ModuleOut(BaseModel):
    id: int
    key: str
    name: str
    description: str = ""
    model_path: str = ""
    model_filename: str = ""
    model_version: str = "v1"
    architecture: str = ""
    file_size_mb: float = 0.0
    class_names: List[str] = []
    num_classes: int = 0
    confidence_threshold: float = 0.65
    cooldown_sec: int = 60
    priority: str = "normal"
    enabled: bool = True
    icon: str = "boxes"
    color: str = "#3b82f6"
    image_url: str = ""
    is_custom: bool = False
    total_detections: int = 0
    avg_inference_ms: float = 0.0
    accuracy_pct: float = 0.0
    last_used_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_db(cls, m: Module) -> "ModuleOut":
        names = []
        try:
            names = json.loads(m.class_names or "[]")
        except Exception:
            names = []
        return cls(
            id=m.id, key=m.key, name=m.name,
            description=m.description or "",
            model_path=m.model_path or "",
            model_filename=getattr(m, "model_filename", "") or "",
            model_version=m.model_version or "v1",
            architecture=getattr(m, "architecture", "") or "",
            file_size_mb=getattr(m, "file_size_mb", 0.0) or 0.0,
            class_names=names,
            num_classes=getattr(m, "num_classes", 0) or 0,
            confidence_threshold=m.confidence_threshold,
            cooldown_sec=m.cooldown_sec,
            priority=m.priority,
            enabled=m.enabled,
            icon=m.icon, color=m.color,
            image_url=getattr(m, "image_url", "") or "",
            is_custom=getattr(m, "is_custom", False) or False,
            total_detections=getattr(m, "total_detections", 0) or 0,
            avg_inference_ms=getattr(m, "avg_inference_ms", 0.0) or 0.0,
            accuracy_pct=getattr(m, "accuracy_pct", 0.0) or 0.0,
            last_used_at=getattr(m, "last_used_at", None),
            created_at=getattr(m, "created_at", None),
            updated_at=getattr(m, "updated_at", None),
        )


class ModuleCreateIn(BaseModel):
    key: str
    name: str
    description: str = ""
    confidence_threshold: float = 0.65
    cooldown_sec: int = 60
    priority: str = "normal"
    icon: str = "boxes"
    color: str = "#3b82f6"
    image_url: str = ""


class ModuleUpdateIn(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    confidence_threshold: Optional[float] = None
    cooldown_sec: Optional[int] = None
    priority: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    image_url: Optional[str] = None
    enabled: Optional[bool] = None


# ============ Helpers ============

def _sanitize_filename(name: str) -> str:
    name = os.path.basename(name or "")
    name = re.sub(r"[^a-zA-Z0-9._-]", "_", name)
    if not name.endswith(".pt"):
        name += ".pt"
    return name


def _inspect_pt(file_path: Path) -> dict:
    """Try to read .pt metadata: architecture (YOLOv8n/s/m/l), class names.
    Falls back gracefully when ultralytics not installed."""
    info = {"architecture": "", "class_names": [], "num_classes": 0, "valid": True}

    if HAS_ULTRALYTICS:
        try:
            model = YOLO(str(file_path))
            try:
                names_dict = getattr(model.model, "names", None) or getattr(model, "names", None) or {}
                if isinstance(names_dict, dict):
                    names = [names_dict[i] for i in sorted(names_dict.keys())]
                elif isinstance(names_dict, list):
                    names = list(names_dict)
                else:
                    names = []
                info["class_names"] = [str(n) for n in names]
                info["num_classes"] = len(names)
            except Exception:
                pass
            # Try architecture detection from model.yaml or task
            try:
                yaml = getattr(model.model, "yaml", {}) or {}
                if isinstance(yaml, dict):
                    arch_str = yaml.get("scale") or yaml.get("model", "")
                    if arch_str:
                        info["architecture"] = f"YOLOv8{arch_str}" if len(arch_str) == 1 else str(arch_str)
            except Exception:
                pass
            # Fall back: guess from file size
            if not info["architecture"]:
                size_mb = file_path.stat().st_size / (1024 * 1024)
                if size_mb < 8:
                    info["architecture"] = "YOLOv8n"
                elif size_mb < 25:
                    info["architecture"] = "YOLOv8s"
                elif size_mb < 60:
                    info["architecture"] = "YOLOv8m"
                elif size_mb < 100:
                    info["architecture"] = "YOLOv8l"
                else:
                    info["architecture"] = "YOLOv8x"
        except Exception as e:
            print(f"[Modules] ultralytics validation failed: {e}")
            info["valid"] = False
    elif HAS_TORCH:
        # Try basic torch.load to verify it's a valid checkpoint
        try:
            import torch as _t
            ckpt = _t.load(str(file_path), map_location="cpu", weights_only=False)
            if isinstance(ckpt, dict):
                names = ckpt.get("names") or {}
                if isinstance(names, dict):
                    info["class_names"] = [str(names[i]) for i in sorted(names.keys())]
                elif isinstance(names, list):
                    info["class_names"] = [str(n) for n in names]
                info["num_classes"] = len(info["class_names"])
        except Exception as e:
            print(f"[Modules] torch.load failed: {e}")
            info["valid"] = False
    else:
        # No deps installed — accept the file and let the user proceed
        size_mb = file_path.stat().st_size / (1024 * 1024)
        info["architecture"] = "YOLOv8" if size_mb < 100 else "Custom"
    return info


def _slug(s: str) -> str:
    s = (s or "").lower().strip()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s or "module"


# ============ Endpoints ============

@router.get("", response_model=List[ModuleOut])
async def list_modules(db: AsyncSession = Depends(get_db), current: User = Depends(get_current_user)):
    res = await db.execute(select(Module).order_by(Module.id))
    return [ModuleOut.from_db(m) for m in res.scalars().all()]


@router.get("/{module_id}", response_model=ModuleOut)
async def get_module(module_id: int, db: AsyncSession = Depends(get_db), current: User = Depends(get_current_user)):
    m = await db.get(Module, module_id)
    if not m:
        raise HTTPException(404, "Modul topilmadi")
    return ModuleOut.from_db(m)


@router.post("", response_model=ModuleOut, status_code=201)
async def create_module(
    data: ModuleCreateIn,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Create a new module record. .pt and image can be uploaded separately afterwards."""
    key = _slug(data.key)
    # Ensure unique key
    existing = await db.execute(select(Module).where(Module.key == key))
    if existing.scalar_one_or_none():
        raise HTTPException(400, f"'{key}' kalit allaqachon mavjud")
    m = Module(
        key=key, name=data.name.strip(),
        description=(data.description or "").strip(),
        confidence_threshold=max(0.1, min(0.99, data.confidence_threshold)),
        cooldown_sec=max(5, data.cooldown_sec),
        priority=data.priority,
        icon=data.icon or "boxes",
        color=data.color or "#3b82f6",
        image_url=data.image_url or "",
        is_custom=True,
        enabled=True,
    )
    db.add(m)
    await db.commit()
    await db.refresh(m)
    return ModuleOut.from_db(m)


@router.put("/{module_id}", response_model=ModuleOut)
async def update_module(
    module_id: int, data: ModuleUpdateIn,
    db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin),
):
    m = await db.get(Module, module_id)
    if not m:
        raise HTTPException(404, "Modul topilmadi")
    if data.name is not None:
        m.name = data.name.strip()
    if data.description is not None:
        m.description = data.description.strip()
    if data.confidence_threshold is not None:
        m.confidence_threshold = max(0.1, min(0.99, data.confidence_threshold))
    if data.cooldown_sec is not None:
        m.cooldown_sec = max(5, data.cooldown_sec)
    if data.priority is not None:
        m.priority = data.priority
    if data.icon is not None:
        m.icon = data.icon
    if data.color is not None:
        m.color = data.color
    if data.image_url is not None:
        m.image_url = data.image_url
    if data.enabled is not None:
        m.enabled = data.enabled
    m.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(m)
    return ModuleOut.from_db(m)


@router.post("/{module_id}/toggle", response_model=ModuleOut)
async def toggle_module(module_id: int, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    m = await db.get(Module, module_id)
    if not m:
        raise HTTPException(404, "Modul topilmadi")
    m.enabled = not m.enabled
    m.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(m)
    return ModuleOut.from_db(m)


@router.delete("/{module_id}", status_code=204)
async def delete_module(module_id: int, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    m = await db.get(Module, module_id)
    if not m:
        raise HTTPException(404, "Modul topilmadi")
    # Remove .pt file
    if m.model_path:
        try:
            p = Path(m.model_path)
            if p.exists() and p.is_file() and MODELS_DIR in p.parents:
                p.unlink()
        except Exception as e:
            print(f"[Modules] failed to delete .pt: {e}")
    # Remove image
    if m.image_url and m.image_url.startswith("/api/modules/images/"):
        try:
            img_name = m.image_url.split("/")[-1]
            img_path = MODULE_IMG_DIR / img_name
            if img_path.exists():
                img_path.unlink()
        except Exception:
            pass
    await db.delete(m)
    await db.commit()


@router.post("/{module_id}/upload-model", response_model=ModuleOut)
async def upload_model_to_module(
    module_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Upload (or replace) the .pt file for a module."""
    m = await db.get(Module, module_id)
    if not m:
        raise HTTPException(404, "Modul topilmadi")
    if not (file.filename or "").lower().endswith(".pt"):
        raise HTTPException(400, "Faqat .pt fayllar qabul qilinadi")

    # Save with versioned filename based on module key
    base = _slug(m.key)
    safe = _sanitize_filename(file.filename or "")
    # Unique-ify with module key prefix
    final_name = f"{base}_{uuid_lib.uuid4().hex[:6]}.pt"
    dest = MODELS_DIR / final_name

    content = await file.read()
    if len(content) > 500 * 1024 * 1024:  # 500 MB safety limit
        raise HTTPException(400, "Fayl 500 MB dan katta")
    dest.write_bytes(content)
    size_mb = round(len(content) / (1024 * 1024), 2)

    # Validate / extract metadata
    info = _inspect_pt(dest)
    if not info["valid"]:
        # Don't keep an invalid file
        try:
            dest.unlink()
        except Exception:
            pass
        raise HTTPException(400, "Yaroqsiz .pt fayl — yuklab bo'lmadi")

    # Remove old .pt if present
    if m.model_path:
        try:
            old = Path(m.model_path)
            if old.exists() and old.is_file() and MODELS_DIR in old.parents:
                old.unlink()
        except Exception:
            pass

    m.model_path = str(dest)
    m.model_filename = safe
    m.file_size_mb = size_mb
    m.architecture = info["architecture"]
    m.class_names = json.dumps(info["class_names"], ensure_ascii=False)
    m.num_classes = info["num_classes"]
    # Bump version
    try:
        v = int(re.sub(r"[^0-9]", "", m.model_version or "1") or "1")
        m.model_version = f"v{v + 1}"
    except Exception:
        m.model_version = "v2"
    m.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(m)

    return ModuleOut.from_db(m)


@router.post("/{module_id}/upload-image", response_model=ModuleOut)
async def upload_image_to_module(
    module_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    m = await db.get(Module, module_id)
    if not m:
        raise HTTPException(404, "Modul topilmadi")
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        raise HTTPException(400, "Rasm formati noto'g'ri (jpg/png/webp/gif)")
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(400, "Rasm 10 MB dan katta")
    fname = f"mod_{m.id}_{uuid_lib.uuid4().hex[:8]}{ext}"
    fpath = MODULE_IMG_DIR / fname

    # Delete old image if managed by us
    if m.image_url and m.image_url.startswith("/api/modules/images/"):
        try:
            old = MODULE_IMG_DIR / m.image_url.split("/")[-1]
            if old.exists():
                old.unlink()
        except Exception:
            pass

    fpath.write_bytes(content)
    m.image_url = f"/api/modules/images/{fname}"
    m.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(m)
    return ModuleOut.from_db(m)


@router.delete("/{module_id}/image", response_model=ModuleOut)
async def remove_image(module_id: int, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    m = await db.get(Module, module_id)
    if not m:
        raise HTTPException(404, "Modul topilmadi")
    if m.image_url and m.image_url.startswith("/api/modules/images/"):
        try:
            old = MODULE_IMG_DIR / m.image_url.split("/")[-1]
            if old.exists():
                old.unlink()
        except Exception:
            pass
    m.image_url = ""
    m.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(m)
    return ModuleOut.from_db(m)


@router.get("/images/{fname}")
async def serve_module_image(fname: str):
    if "/" in fname or "\\" in fname or ".." in fname:
        raise HTTPException(400, "Noto'g'ri fayl nomi")
    fpath = MODULE_IMG_DIR / fname
    if not fpath.exists():
        raise HTTPException(404, "Rasm topilmadi")
    return FileResponse(str(fpath))


@router.get("/{module_id}/download-model")
async def download_model(module_id: int, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    m = await db.get(Module, module_id)
    if not m:
        raise HTTPException(404, "Modul topilmadi")
    if not m.model_path:
        raise HTTPException(404, "Bu modulga .pt fayl yuklanmagan")
    fpath = Path(m.model_path)
    if not fpath.exists():
        raise HTTPException(404, "Fayl yo'q")
    return FileResponse(str(fpath), filename=m.model_filename or fpath.name,
                        media_type="application/octet-stream")


@router.get("/system/info")
async def system_info(current: User = Depends(get_current_user)):
    """Diagnostic info: are ultralytics/torch available?"""
    from app.core import inference as inf
    info = {
        "has_torch": HAS_TORCH,
        "has_ultralytics": HAS_ULTRALYTICS,
        "models_dir": str(MODELS_DIR),
        "model_images_dir": str(MODULE_IMG_DIR),
        "inference": inf.get_status(),
        "workers": inf.workers_status(),
    }
    if HAS_TORCH:
        try:
            import torch
            info["torch_version"] = torch.__version__
            info["cuda_available"] = torch.cuda.is_available()
            if torch.cuda.is_available():
                info["cuda_device"] = torch.cuda.get_device_name(0)
        except Exception:
            pass
    return info
