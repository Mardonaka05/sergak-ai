"""
Alert manager — receives detections, applies cooldown, saves snapshots,
writes to DB, dispatches to notification workers (Telegram, WhatsApp, SMS).
"""
import asyncio
import time
from typing import Dict, Tuple, Any
from pathlib import Path
from datetime import datetime
import numpy as np

# import cv2
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.event import Event


# Per-module priority — affects notification channel
MODULE_PRIORITY = {
    "fire": "critical",
    "fall": "critical",
    "zone": "high",
    "smoking": "high",
    "twoperson": "high",
    "helmet": "normal",
    "phone": "low",
}

MODULE_MESSAGES = {
    "helmet": "Kaska kiyilmagan",
    "phone": "Telefon ishlatish",
    "smoking": "Chekish aniqlandi",
    "fall": "Yiqilish aniqlandi",
    "fire": "Yong'in belgilari aniqlandi",
    "zone": "Cheklangan zonaga kirish",
    "twoperson": "Yolg'iz ishlash",
}


class AlertManager:
    def __init__(self):
        # cooldown key: (camera_id, module) -> last_alert_ts
        self._cooldowns: Dict[Tuple[int, str], float] = {}
        # listeners (e.g. WebSocket broadcasters, telegram bot)
        self._listeners = []

    def add_listener(self, callback):
        """Subscribe a function that gets called with each new event"""
        self._listeners.append(callback)

    async def submit(self, camera_id: int, camera_name: str, module: str,
                     confidence: float, bbox: tuple, frame: np.ndarray,
                     cooldown_sec: int = 60):
        """Handle a single detection — debounce, save, notify."""
        key = (camera_id, module)
        now = time.time()
        last = self._cooldowns.get(key, 0)
        if now - last < cooldown_sec:
            return  # in cooldown — drop
        self._cooldowns[key] = now

        priority = MODULE_PRIORITY.get(module, "normal")
        critical = priority == "critical"
        message = MODULE_MESSAGES.get(module, f"{module} aniqlandi")

        # Save snapshot with bounding box overlay
        snap_path = await self._save_snapshot(camera_id, camera_name, module, frame, bbox, confidence)

        # Persist event
        async with AsyncSessionLocal() as db:
            e = Event(
                camera_id=camera_id,
                module_name=module,
                message=message,
                confidence=confidence,
                snapshot_path=str(snap_path),
                critical=critical,
                timestamp=datetime.utcnow(),
            )
            db.add(e)
            await db.commit()
            await db.refresh(e)

        # Notify all listeners
        for cb in self._listeners:
            try:
                await cb({
                    "id": e.id, "camera_id": camera_id, "camera_name": camera_name,
                    "module": module, "message": message, "confidence": confidence,
                    "snapshot_path": str(snap_path), "critical": critical,
                    "priority": priority, "timestamp": e.timestamp.isoformat(),
                })
            except Exception as ex:
                print(f"[AlertManager] listener error: {ex}")

    async def _save_snapshot(self, camera_id, camera_name, module, frame, bbox, conf) -> Path:
        """Save annotated snapshot to disk: snapshots/YYYY-MM-DD/camN_module_HHMM.jpg"""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        time_str = datetime.utcnow().strftime("%Hh%M%S")
        out_dir = settings.SNAPSHOTS_DIR / today
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"cam{camera_id}_{module}_{time_str}.jpg"
        # In production:
        #   annotated = frame.copy()
        #   x1, y1, x2, y2 = bbox
        #   cv2.rectangle(annotated, (x1,y1), (x2,y2), (0,0,255), 3)
        #   label = f"{module.upper()} {conf:.0%}"
        #   cv2.putText(annotated, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
        #   # Add dept + camera + timestamp watermark
        #   cv2.imwrite(str(path), annotated)
        return path
