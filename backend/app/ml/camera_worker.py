"""
Camera worker process — reads RTSP stream, runs AI on each frame,
emits detections to AlertManager via queue.
One CameraWorker per physical camera.
"""
import asyncio
import time
import numpy as np
from pathlib import Path
from typing import List, Dict, Any

# import cv2  # On Jetson
from app.ml.inference import engine, Detection
from app.ml.alert_manager import AlertManager
from app.core.config import settings


class MotionDetector:
    """Simple motion detector — skip inference on empty frames (saves 70% GPU)"""
    def __init__(self, threshold: float = 25.0):
        self.prev = None
        self.threshold = threshold

    def has_motion(self, frame: np.ndarray) -> bool:
        if self.prev is None:
            self.prev = frame
            return True
        diff = np.abs(frame.astype(int) - self.prev.astype(int)).mean()
        self.prev = frame
        return diff > self.threshold


class CameraWorker:
    """
    One worker per RTSP camera. Pulls frames, runs inference, pushes events.
    On Jetson, use GStreamer hardware-accelerated decode:
        rtspsrc location=<url> ! rtph264depay ! h264parse !
        nvv4l2decoder ! nvvidconv ! video/x-raw,format=BGRx !
        videoconvert ! video/x-raw,format=BGR ! appsink
    """
    def __init__(self, camera_id: int, name: str, rtsp_url: str,
                 modules_enabled: List[str], polygons: List[Dict[str, Any]],
                 confidence: float, cooldown: int, alert_mgr: AlertManager):
        self.camera_id = camera_id
        self.name = name
        self.rtsp_url = rtsp_url
        self.modules_enabled = modules_enabled
        self.polygons = polygons
        self.confidence = confidence
        self.cooldown = cooldown
        self.alert_mgr = alert_mgr
        self.fps_target = 15
        self.frame_skip = settings.FRAME_SKIP
        self.motion = MotionDetector() if settings.MOTION_TRIGGERED else None
        self.running = False

    async def run(self):
        """Main loop — RTSP → frame → AI → alerts"""
        self.running = True
        # cap = cv2.VideoCapture(self._gstreamer_pipeline(), cv2.CAP_GSTREAMER)
        # In production, recover from disconnects with exponential backoff
        frame_counter = 0
        last_log = time.time()
        fps_count = 0

        while self.running:
            # ret, frame = cap.read()
            # if not ret:
            #     await asyncio.sleep(1)
            #     continue
            frame = np.zeros((1080, 1920, 3), dtype=np.uint8)  # stub

            frame_counter += 1
            fps_count += 1

            # Skip frames according to settings
            if frame_counter % self.frame_skip != 0:
                await asyncio.sleep(0.01)
                continue

            # Motion-triggered: skip empty frames
            if self.motion and not self.motion.has_motion(frame):
                await asyncio.sleep(0.01)
                continue

            # Run all enabled modules on this frame
            detections_per_module = engine.run_all_enabled(frame, self.modules_enabled)

            # Forward to alert manager
            for module_key, dets in detections_per_module.items():
                for det in dets:
                    if det.confidence < self.confidence:
                        continue
                    # Check restricted zones for zone module
                    if module_key == "zone":
                        if not self._point_in_any_polygon(self._foot_point(det.bbox)):
                            continue
                    await self.alert_mgr.submit(
                        camera_id=self.camera_id,
                        camera_name=self.name,
                        module=module_key,
                        confidence=det.confidence,
                        bbox=det.bbox,
                        frame=frame,
                    )

            # FPS log
            if time.time() - last_log > 5:
                print(f"[Camera {self.name}] {fps_count/5:.1f} FPS")
                fps_count = 0
                last_log = time.time()

            await asyncio.sleep(0)  # yield to event loop

    def stop(self):
        self.running = False

    def _gstreamer_pipeline(self) -> str:
        """Hardware-accelerated RTSP decode on Jetson"""
        return (
            f"rtspsrc location={self.rtsp_url} latency=100 ! "
            f"rtph264depay ! h264parse ! nvv4l2decoder ! "
            f"nvvidconv ! video/x-raw,format=BGRx ! "
            f"videoconvert ! video/x-raw,format=BGR ! appsink drop=true sync=false"
        )

    @staticmethod
    def _foot_point(bbox):
        x1, y1, x2, y2 = bbox
        return ((x1 + x2) // 2, y2)

    def _point_in_any_polygon(self, point) -> bool:
        if not self.polygons:
            return False
        # ray-casting
        x, y = point
        for poly in self.polygons:
            pts = poly.get("points", [])
            if self._point_in_poly(x, y, pts):
                return True
        return False

    @staticmethod
    def _point_in_poly(x, y, pts):
        n = len(pts)
        inside = False
        j = n - 1
        for i in range(n):
            xi, yi = pts[i]
            xj, yj = pts[j]
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi):
                inside = not inside
            j = i
        return inside
