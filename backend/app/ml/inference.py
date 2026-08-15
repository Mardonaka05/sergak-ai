"""
YOLOv8 inference wrapper — loads .pt or .engine, runs detection.
Supports per-module models OR a single combined model.
"""
from typing import List, Dict, Tuple
import numpy as np
from pathlib import Path


class Detection:
    """Single object detection"""
    __slots__ = ("class_name", "confidence", "bbox")
    def __init__(self, class_name: str, confidence: float, bbox: Tuple[int, int, int, int]):
        self.class_name = class_name
        self.confidence = confidence
        self.bbox = bbox  # x1, y1, x2, y2

    def as_dict(self):
        return {"class": self.class_name, "confidence": self.confidence, "bbox": list(self.bbox)}


class YoloModel:
    """
    Wrapper around Ultralytics YOLOv8 model.
    On Jetson, prefer TensorRT .engine (FP16) for 3-5x speedup.
    """
    def __init__(self, model_path: str, confidence: float = 0.65, device: str = "cuda:0"):
        self.model_path = model_path
        self.confidence = confidence
        self.device = device
        self._model = None

    def load(self):
        """Lazy-load model — on Jetson:
            from ultralytics import YOLO
            self._model = YOLO(self.model_path)
        """
        if not Path(self.model_path).exists():
            print(f"[YoloModel] Warning: {self.model_path} not found, using stub")
            return
        # from ultralytics import YOLO
        # self._model = YOLO(self.model_path)
        # if self.model_path.endswith('.pt') and self.device.startswith('cuda'):
        #     # auto-export to TensorRT on first load
        #     self._model.export(format='engine', half=True, device=0)
        pass

    def infer(self, frame: np.ndarray) -> List[Detection]:
        """Run inference on one BGR frame, return list of Detection."""
        if self._model is None:
            # Stub: return empty until real model loaded
            return []
        # results = self._model(frame, conf=self.confidence, verbose=False, device=self.device)
        # detections = []
        # for r in results:
        #     for box in r.boxes:
        #         x1, y1, x2, y2 = box.xyxy[0].tolist()
        #         cls = r.names[int(box.cls[0])]
        #         conf = float(box.conf[0])
        #         detections.append(Detection(cls, conf, (int(x1), int(y1), int(x2), int(y2))))
        # return detections
        return []

    def infer_batch(self, frames: List[np.ndarray]) -> List[List[Detection]]:
        """Batched inference — much more efficient on GPU"""
        return [self.infer(f) for f in frames]


class InferenceEngine:
    """
    Manages all loaded modules. Each module = one .pt model.
    """
    def __init__(self):
        self.models: Dict[str, YoloModel] = {}

    def register(self, key: str, model_path: str, confidence: float = 0.65):
        m = YoloModel(model_path, confidence)
        m.load()
        self.models[key] = m
        print(f"[InferenceEngine] Loaded module '{key}' from {model_path}")

    def run_module(self, key: str, frame: np.ndarray) -> List[Detection]:
        if key not in self.models: return []
        return self.models[key].infer(frame)

    def run_all_enabled(self, frame: np.ndarray, enabled_modules: List[str]) -> Dict[str, List[Detection]]:
        """Run all enabled modules on the same frame"""
        return {k: self.run_module(k, frame) for k in enabled_modules if k in self.models}


# Singleton
engine = InferenceEngine()


def init_inference_engine(models_dir: Path):
    """Auto-discover .pt files in models_dir and register them by filename"""
    for pt in models_dir.glob("*.pt"):
        key = pt.stem.split("_")[0]  # 'helmet_v2.pt' -> 'helmet'
        engine.register(key, str(pt))
