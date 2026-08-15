"""
best.pt ni production-ready holatga keltirish:
  - Optimizer state ni olib tashlaydi (-170 MB)
  - EMA weights ni olib tashlaydi (-85 MB)
  - Faqat model weights qoladi (~85 MB)

Natija: 350 MB -> 85 MB (4x kichikroq!)

Ishlatish:
  python scripts/export_production.py
"""
import torch
from pathlib import Path
from ultralytics import YOLO

ROOT = Path(r"D:\sergak dasturi\kaska")
SRC = ROOT / "runs" / "helmet_v8l_640" / "weights" / "best.pt"
DST_LEAN = ROOT / "runs" / "helmet_v8l_640" / "weights" / "best_production.pt"
DST_BACKEND = ROOT.parent / "backend" / "models" / "sergak_helmet_v1_94mAP.pt"


def main():
    if not SRC.exists():
        print(f"[X] Topilmadi: {SRC}")
        return

    print("=" * 70)
    print("  Sergak AI - Production Model Export")
    print("=" * 70)
    print()

    src_size = SRC.stat().st_size / 1e6
    print(f"  Manba:    {SRC.name}  ({src_size:.1f} MB)")

    # Ultralytics ning RASMIY strip_optimizer usuli
    # Optimizer, EMA, training metadata - hammasini olib tashlaydi
    from ultralytics.utils.torch_utils import strip_optimizer
    import shutil

    # Avval src ni dst ga ko'chiramiz
    shutil.copy2(str(SRC), str(DST_LEAN))
    # Keyin strip_optimizer ni ishlatamiz
    strip_optimizer(str(DST_LEAN))

    dst_size = DST_LEAN.stat().st_size / 1e6
    print(f"  Production: {DST_LEAN.name}  ({dst_size:.1f} MB)")
    if dst_size > 0:
        print(f"  Kichraydi:  {src_size:.1f} MB -> {dst_size:.1f} MB ({src_size/dst_size:.1f}x)")
    print()

    # Sergak AI backend papkasiga ko'chirish
    DST_BACKEND.parent.mkdir(parents=True, exist_ok=True)
    try:
        import shutil
        shutil.copy2(str(DST_LEAN), str(DST_BACKEND))
        print(f"  [OK] Backend ga ko'chirildi: {DST_BACKEND}")
    except Exception as e:
        print(f"  [!] Backend ga ko'chirish xato: {e}")
        print(f"      Qo'lda ko'chiring: copy \"{DST_LEAN}\" \"{DST_BACKEND}\"")

    # Test - production model ham ishlaydimi?
    print()
    print("=" * 70)
    print("  Sinov - production model yuklab ko'rish")
    print("=" * 70)
    try:
        test_model = YOLO(str(DST_LEAN))
        info = test_model.info(verbose=False)
        print(f"  [OK] Model muvaffaqiyatli yuklandi")
        print(f"  Layers:   {info[0]}")
        print(f"  Params:   {info[1]:,}")
        print(f"  GFLOPs:   {info[3]:.1f}")
    except Exception as e:
        print(f"  [X] Yuklashda xato: {e}")

    print()
    print("=" * 70)
    print("  TUGADI")
    print("=" * 70)
    print(f"  Production fayl: {DST_LEAN}")
    print(f"  Backend fayli:   {DST_BACKEND}")
    print()


if __name__ == "__main__":
    main()
