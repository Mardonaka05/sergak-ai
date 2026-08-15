"""
Trainingdan keyin model sinab ko'rish.

Test split dan tasodifiy 20 ta rasm olib, modelni ishlatadi va natijalarni
runs/predict_test/ papkasiga saqlaydi (bbox bilan chizilgan).
"""
import random
import sys
from pathlib import Path

# ---- Konfiguratsiya ----
WEIGHTS = Path(r"D:\sergak dasturi\kaska\runs\helmet_v8l_640\weights\best.pt")
TEST_DIR = Path(r"D:\sergak dasturi\kaska\merged\images\test")
OUTPUT_DIR = Path(r"D:\sergak dasturi\kaska\runs\predict_test")
N_SAMPLES = 20
CONF = 0.25  # confidence threshold


def main():
    try:
        from ultralytics import YOLO
    except ImportError:
        print("[X] ultralytics yo'q. pip install ultralytics")
        sys.exit(1)

    if not WEIGHTS.exists():
        print(f"[X] Model vazn fayli topilmadi: {WEIGHTS}")
        print(f"    Avval treningni tugating: 7_train.bat")
        sys.exit(1)

    if not TEST_DIR.exists():
        print(f"[X] Test papka topilmadi: {TEST_DIR}")
        sys.exit(1)

    print("=" * 70)
    print(f"  Model: {WEIGHTS.name}")
    print(f"  Test: {TEST_DIR}")
    print(f"  Confidence: {CONF}")
    print("=" * 70)

    # Tasodifiy rasmlar
    all_imgs = [p for p in TEST_DIR.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png")]
    random.seed(42)
    samples = random.sample(all_imgs, min(N_SAMPLES, len(all_imgs)))
    print(f"  Tanlangan: {len(samples)} ta rasm\n")

    model = YOLO(str(WEIGHTS))

    # Inference
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results = model(
        [str(p) for p in samples],
        conf=CONF,
        save=True,
        project=str(OUTPUT_DIR.parent),
        name=OUTPUT_DIR.name,
        exist_ok=True,
        verbose=False,
    )

    # Statistika
    total_helmet = 0
    total_no_helmet = 0
    for i, (p, r) in enumerate(zip(samples, results)):
        boxes = r.boxes
        h = (boxes.cls == 0).sum().item() if boxes is not None else 0
        nh = (boxes.cls == 1).sum().item() if boxes is not None else 0
        total_helmet += h
        total_no_helmet += nh
        print(f"  [{i+1:2d}] {p.name:40s}  helmet={h}  no_helmet={nh}")

    print()
    print("=" * 70)
    print(f"  JAMI: helmet={total_helmet}  no_helmet={total_no_helmet}")
    print(f"  Natijalar: {OUTPUT_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()
