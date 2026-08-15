"""YOLOv8 inference engine — runs uploaded .pt models against camera RTSP streams.

Gracefully degrades when ultralytics/opencv aren't installed (returns False from start()
and the rest of the app keeps working — only the AI inference is disabled).

Design:
  * Each (camera, module) pair becomes a "task" that runs in a background thread
  * The thread reads RTSP frames with OpenCV, runs YOLO inference, and writes
    detections to the `events` table with a cooldown between repeated alerts
  * Confidence threshold, cooldown_sec, and class filtering come from the Module row
  * Models are loaded once per .pt path and cached in-process
"""
import asyncio
import json
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Bostirish: FFmpeg HEVC dekoder shovqinlari (PPS, POC, NAL warnings)
# Bu kameralar oqimi yaxshi ishlayotgan paytda ham chiqadi va keraksiz
os.environ["OPENCV_FFMPEG_LOGLEVEL"] = "-8"  # AV_LOG_QUIET
os.environ["OPENCV_LOG_LEVEL"] = "ERROR"

# Optional native deps. The platform still works without them — inference is just
# disabled until they're installed (pip install ultralytics opencv-python).
try:
    import cv2  # type: ignore
    HAS_OPENCV = True
    # Yana bir bostirish — OpenCV log darajasi
    try:
        cv2.setLogLevel(3)  # 3 = ERROR
    except Exception:
        pass
except Exception:
    HAS_OPENCV = False

try:
    from ultralytics import YOLO  # type: ignore
    HAS_ULTRALYTICS = True
except Exception:
    HAS_ULTRALYTICS = False

try:
    import torch  # type: ignore
    HAS_TORCH = True
    HAS_CUDA = torch.cuda.is_available()
    CUDA_DEVICE = "cuda:0" if HAS_CUDA else "cpu"
    if HAS_CUDA:
        gpu_name = torch.cuda.get_device_name(0)
        gpu_mem = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"[Inference] GPU FAOL: {gpu_name} ({gpu_mem:.1f} GB)")
    else:
        print("[Inference] CPU rejim (GPU mavjud emas - sekinroq ishlaydi)")
except Exception:
    HAS_TORCH = False
    HAS_CUDA = False
    CUDA_DEVICE = "cpu"


# Inference sozlamalari — tezlik uchun
INFER_DEVICE = CUDA_DEVICE  # "cuda:0" yoki "cpu"
INFER_HALF = HAS_CUDA       # FP16 — faqat GPU'da (2x tezroq)
INFER_IMGSZ = 640           # YOLOv8 standart kirish o'lchami (frame resize qilinadi)

# ============ RESURS CHEKLOVLARI (kompyuter qotib qolmasligi uchun) ============
# Bir vaqtning o'zida nechta inference ishlay oladi. RTX 4060 8GB uchun 4 ta optimal.
# CPU rejimida — 1 ta (sekin lekin xavfsiz).
_MAX_CONCURRENT_INFER = 4 if HAS_CUDA else 1
_INFER_SEMAPHORE = threading.Semaphore(_MAX_CONCURRENT_INFER)

# CPU/GPU ga moslab frame skip (yuqori = kam tahlil, kichik yuk)
_DEFAULT_FRAME_SKIP_GPU = 5     # GPU: har 5-kadr (taxminan 5-6 FPS analiz)
_DEFAULT_FRAME_SKIP_CPU = 30    # CPU: har 30-kadr (1 FPS analiz — ozgina yuk)


# In-process YOLO cache
_MODEL_CACHE: Dict[str, object] = {}

# Latest frames per camera (as JPEG bytes) — for live preview snapshots
_LATEST_FRAMES: Dict[int, bytes] = {}
_FRAMES_LOCK = threading.Lock()


def get_latest_frame_jpeg(camera_id: int) -> Optional[bytes]:
    """Return latest frame for camera as JPEG bytes (None if not available)."""
    with _FRAMES_LOCK:
        return _LATEST_FRAMES.get(camera_id)


def _save_frame_jpeg(camera_id: int, frame):
    """Encode frame as JPEG and save in shared dict."""
    if not HAS_OPENCV: return
    try:
        ok, buf = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
        if ok:
            with _FRAMES_LOCK:
                _LATEST_FRAMES[camera_id] = buf.tobytes()
    except Exception:
        pass


def is_available() -> bool:
    return HAS_OPENCV and HAS_ULTRALYTICS


def get_status() -> dict:
    """Diagnostic info returned by /api/modules/system/info too."""
    info = {
        "has_opencv": HAS_OPENCV,
        "has_ultralytics": HAS_ULTRALYTICS,
        "has_torch": HAS_TORCH,
        "has_cuda": HAS_CUDA,
        "device": INFER_DEVICE,
        "half_precision": INFER_HALF,
        "imgsz": INFER_IMGSZ,
        "available": is_available(),
        "models_loaded": len(_MODEL_CACHE),
        "loaded_paths": list(_MODEL_CACHE.keys()),
    }
    if HAS_CUDA:
        try:
            import torch
            info["gpu_name"] = torch.cuda.get_device_name(0)
            info["gpu_memory_gb"] = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2)
            info["gpu_mem_allocated_gb"] = round(torch.cuda.memory_allocated(0) / (1024**3), 2)
        except Exception:
            pass
    return info


def load_model(model_path: str):
    """Load a YOLO model (cached) + move to GPU + warm-up."""
    if not HAS_ULTRALYTICS:
        return None
    p = str(Path(model_path).resolve())
    if p in _MODEL_CACHE:
        return _MODEL_CACHE[p]
    try:
        m = YOLO(p)
        # GPU ga ko'chirish (mavjud bo'lsa)
        if HAS_CUDA:
            try:
                m.to(INFER_DEVICE)
                print(f"[Inference] Loaded -> {INFER_DEVICE}: {Path(p).name}")
            except Exception as e:
                print(f"[Inference] GPU ga ko'chira olmadi, CPU: {Path(p).name} ({e})")
        else:
            print(f"[Inference] Loaded (CPU): {Path(p).name}")

        # Warm-up - birinchi inference 2-3x sekin bo'ladi
        try:
            import numpy as np
            dummy = np.zeros((INFER_IMGSZ, INFER_IMGSZ, 3), dtype=np.uint8)
            _ = m.predict(dummy, conf=0.5, device=INFER_DEVICE,
                          half=INFER_HALF, imgsz=INFER_IMGSZ, verbose=False)
            print(f"[Inference]   warm-up tugadi: {Path(p).name}")
        except Exception as e:
            print(f"[Inference]   warm-up xato: {e}")

        _MODEL_CACHE[p] = m
        return m
    except Exception as e:
        print(f"[Inference] Failed to load {p}: {e}")
        return None


def unload_model(model_path: str):
    p = str(Path(model_path).resolve())
    if p in _MODEL_CACHE:
        del _MODEL_CACHE[p]


# ============ Worker thread ============

class CameraModuleWorker(threading.Thread):
    """One worker per (camera, module) pair, runs in a daemon thread."""

    def __init__(self, camera_id: int, camera_rtsp: str, module_id: int,
                 model_path: str, confidence_threshold: float,
                 cooldown_sec: int, class_names: List[str],
                 frame_skip: int = 5):
        super().__init__(daemon=True, name=f"infer-{camera_id}-{module_id}")
        self.camera_id = camera_id
        self.camera_rtsp = camera_rtsp
        self.module_id = module_id
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.cooldown_sec = cooldown_sec
        self.class_names = class_names
        self.frame_skip = frame_skip
        self.running = True
        self._stop = threading.Event()
        self.last_alert_at: float = 0
        self.frames_processed = 0
        self.detections_count = 0
        self.last_inference_ms: float = 0
        self.last_error: str = ""

    def stop(self):
        self.running = False
        self._stop.set()

    def run(self):
        if not is_available():
            print(f"[Worker] inference deps unavailable, skip cam={self.camera_id} mod={self.module_id}")
            return
        model = load_model(self.model_path)
        if not model:
            print(f"[Worker] no model for cam={self.camera_id} mod={self.module_id}")
            return

        cap = None
        reconnect_delay = 2.0
        try:
            while self.running and not self._stop.is_set():
                if cap is None or not cap.isOpened():
                    if cap:
                        try: cap.release()
                        except Exception: pass
                    try:
                        cap = cv2.VideoCapture(self.camera_rtsp, cv2.CAP_FFMPEG)
                        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    except Exception as e:
                        self.last_error = str(e)
                        if self._stop.wait(reconnect_delay): break
                        reconnect_delay = min(reconnect_delay * 1.5, 30)
                        continue
                    if not cap.isOpened():
                        self.last_error = f"Cannot open RTSP: {self.camera_rtsp}"
                        if self._stop.wait(reconnect_delay): break
                        reconnect_delay = min(reconnect_delay * 1.5, 30)
                        continue
                    reconnect_delay = 2.0
                    self.last_error = ""

                # Skip frames to keep up with realtime
                for _ in range(self.frame_skip):
                    cap.grab()
                ret, frame = cap.read()
                if not ret or frame is None:
                    self.last_error = "RTSP read failed"
                    try: cap.release()
                    except Exception: pass
                    cap = None
                    continue

                # Live preview uchun snapshot saqlash (har 30-chi kadrda)
                self.frames_processed += 1
                if self.frames_processed % 30 == 0:
                    _save_frame_jpeg(self.camera_id, frame)

                t0 = time.perf_counter()
                # RESURS CHEKLOVI — semaphore bilan parallel inference cheklash
                # Bu kompyuter qotib qolmasligi uchun MUHIM (RTX 4060 8GB)
                got_slot = _INFER_SEMAPHORE.acquire(timeout=5.0)
                if not got_slot:
                    self.last_error = "Inference slot timeout (GPU band)"
                    if self._stop.wait(0.5): break
                    continue
                results = None
                try:
                    # GPU + FP16 + 640px resize - bu kombinatsiya eng tez ishlaydi
                    results = model.predict(
                        frame,
                        conf=self.confidence_threshold,
                        device=INFER_DEVICE,
                        half=INFER_HALF,
                        imgsz=INFER_IMGSZ,
                        verbose=False,
                    )
                except Exception as e:
                    self.last_error = f"predict failed: {e}"
                finally:
                    _INFER_SEMAPHORE.release()
                if results is None:
                    if self._stop.wait(1.0): break
                    continue
                self.last_inference_ms = (time.perf_counter() - t0) * 1000

                detections = []
                for r in results:
                    boxes = getattr(r, "boxes", None)
                    if boxes is None: continue
                    try:
                        for i, box in enumerate(boxes):
                            cls = int(box.cls[0]) if box.cls is not None else -1
                            conf = float(box.conf[0]) if box.conf is not None else 0.0
                            label = (self.class_names[cls] if 0 <= cls < len(self.class_names)
                                     else (model.names.get(cls, "?") if hasattr(model, "names") else str(cls)))
                            detections.append({"class": label, "confidence": conf, "class_id": cls})
                    except Exception:
                        continue

                if detections and (time.time() - self.last_alert_at) > self.cooldown_sec:
                    self.last_alert_at = time.time()
                    self.detections_count += 1
                    # Record event — call back via the queue
                    on_detection(self.camera_id, self.module_id, detections, frame)

                if self._stop.wait(0.05): break

        finally:
            if cap:
                try: cap.release()
                except Exception: pass


# ============ Detection sink ============

_detection_queue: "asyncio.Queue" = None  # type: ignore
_main_loop: "asyncio.AbstractEventLoop" = None  # type: ignore


def set_main_loop(loop):
    global _main_loop, _detection_queue
    _main_loop = loop
    _detection_queue = asyncio.Queue()


def on_detection(camera_id: int, module_id: int, detections: List[dict], frame=None):
    """Called from worker threads. Pushes detection into asyncio queue for DB write."""
    if _main_loop and _detection_queue:
        try:
            _main_loop.call_soon_threadsafe(
                _detection_queue.put_nowait,
                {
                    "camera_id": camera_id,
                    "module_id": module_id,
                    "detections": detections,
                    "timestamp": datetime.utcnow(),
                }
            )
        except Exception as e:
            print(f"[Inference] enqueue failed: {e}")


async def detection_writer_loop():
    """Async loop: read from queue, write Event rows. Optional snapshot save."""
    from app.core.database import AsyncSessionLocal
    from app.models.event import Event
    from app.models.module import Module as ModuleModel

    while True:
        try:
            if _detection_queue is None:
                await asyncio.sleep(0.5)
                continue
            item = await _detection_queue.get()
            async with AsyncSessionLocal() as db:
                # Find module label
                mod = await db.get(ModuleModel, item["module_id"])
                top = max(item["detections"], key=lambda d: d["confidence"])
                msg = f"{mod.name if mod else 'AI'} — {top['class']}"
                db.add(Event(
                    camera_id=item["camera_id"],
                    module_name=mod.key if mod else "ai",
                    message=msg,
                    confidence=top["confidence"],
                    critical=(mod and mod.priority in ("critical", "high")) or False,
                    timestamp=item["timestamp"],
                    acknowledged=False,
                ))
                # Update module stats
                if mod:
                    mod.total_detections = (mod.total_detections or 0) + 1
                    mod.last_used_at = item["timestamp"]
                await db.commit()
        except Exception as e:
            print(f"[Inference] writer error: {e}")
            await asyncio.sleep(1.0)


# ============ Worker manager ============

_workers: Dict[Tuple[int, int], CameraModuleWorker] = {}
_workers_lock = threading.Lock()


def start_worker(camera_id: int, camera_rtsp: str, module_id: int,
                 model_path: str, confidence_threshold: float, cooldown_sec: int,
                 class_names: List[str]) -> bool:
    if not is_available():
        return False
    if not model_path or not Path(model_path).exists():
        print(f"[Inference] skip start: no model at {model_path}")
        return False
    key = (camera_id, module_id)
    with _workers_lock:
        if key in _workers and _workers[key].is_alive():
            return True
        # .env dagi FRAME_SKIP ni o'qish (CPU rejimida 15-30 yaxshi)
        try:
            from app.core.config import settings as _s
            fs = max(2, int(getattr(_s, "FRAME_SKIP", 5)))
        except Exception:
            fs = 5
        # GPU/CPU ga moslab frame_skip ni avtomatik moslashtirish
        if HAS_CUDA:
            # GPU rejim: 5-kadr (taxminan 5-6 FPS analiz, juda tez)
            fs = max(fs, _DEFAULT_FRAME_SKIP_GPU)
        else:
            # CPU rejim: 30-kadr (1 FPS, kompyuter qotib qolmasligi uchun)
            fs = max(fs, _DEFAULT_FRAME_SKIP_CPU)
        # Ko'p worker bo'lsa, har bir worker uchun frame_skip ni oshirish
        # (29 ta worker × 5 fs = 145 ga teng yuk — kamaytiramiz)
        with _workers_lock:
            current_count = len(_workers)
        if current_count > 10:
            fs = int(fs * 1.5)  # 50% kamroq inference
        if current_count > 20:
            fs = int(fs * 2)    # yana 2x kam
        w = CameraModuleWorker(
            camera_id=camera_id, camera_rtsp=camera_rtsp,
            module_id=module_id, model_path=model_path,
            confidence_threshold=confidence_threshold,
            cooldown_sec=cooldown_sec, class_names=class_names,
            frame_skip=fs,
        )
        _workers[key] = w
        w.start()
        print(f"[Inference] Started worker cam={camera_id} mod={module_id}")
        return True


def stop_worker(camera_id: int, module_id: int):
    key = (camera_id, module_id)
    with _workers_lock:
        w = _workers.pop(key, None)
    if w:
        w.stop()
        print(f"[Inference] Stopped worker cam={camera_id} mod={module_id}")


def stop_all():
    with _workers_lock:
        items = list(_workers.items())
        _workers.clear()
    for _, w in items:
        w.stop()


def workers_status() -> List[dict]:
    out = []
    with _workers_lock:
        for (cam_id, mod_id), w in _workers.items():
            out.append({
                "camera_id": cam_id, "module_id": mod_id,
                "alive": w.is_alive(),
                "frames_processed": w.frames_processed,
                "detections_count": w.detections_count,
                "last_inference_ms": round(w.last_inference_ms, 1),
                "last_error": w.last_error,
            })
    return out


# ============ Sync from DB ============

async def sync_workers():
    """Inspect DB: for every (camera, module) pair where camera.online and
    module.enabled and module has a model_path, start a worker. Stop others."""
    if not is_available():
        return
    from app.core.database import AsyncSessionLocal
    from app.models.camera import Camera
    from app.models.module import Module as ModuleModel
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        cams = (await db.execute(select(Camera).where(Camera.online == True))).scalars().all()
        mods = (await db.execute(select(ModuleModel).where(ModuleModel.enabled == True))).scalars().all()
        mod_by_key = {m.key: m for m in mods}

        desired = set()
        for cam in cams:
            enabled_keys = cam.modules_enabled or []
            if isinstance(enabled_keys, str):
                try: enabled_keys = json.loads(enabled_keys)
                except Exception: enabled_keys = []
            for k in enabled_keys:
                m = mod_by_key.get(k)
                if not m or not m.model_path or not Path(m.model_path).exists():
                    continue
                desired.add((cam.id, m.id))
                try:
                    names = json.loads(m.class_names or "[]")
                except Exception:
                    names = []
                start_worker(
                    camera_id=cam.id, camera_rtsp=cam.rtsp_url,
                    module_id=m.id, model_path=m.model_path,
                    confidence_threshold=m.confidence_threshold,
                    cooldown_sec=m.cooldown_sec, class_names=names,
                )

        with _workers_lock:
            running_keys = list(_workers.keys())
        for key in running_keys:
            if key not in desired:
                stop_worker(*key)
if key not in desired:
                stop_worker(*key)
