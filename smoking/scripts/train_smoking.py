"""
SERGAK AI - SIGARET ANIQLASH TRAINING (1 KLASS)
=================================================
Kaska best.pt'dan TRANSFER LEARNING bilan tezroq konvergensiya.

Default:
  Model:    YOLOv8l (kaska best.pt'dan boshlanadi)
  Image:    640
  Batch:    6 (RTX 4060 Laptop 8GB uchun)
  Epochs:   100 (transfer learning bilan tez)
  AMP:      YOQ (mixed precision)
  Classes:  1 (smoking)

Ishlatish:
  python scripts/train_smoking.py
  python scripts/train_smoking.py --resume
  python scripts/train_smoking.py --epochs 50  (qisqartirish)
"""
import argparse
import sys
from pathlib import Path

DATA_YAML = Path(r"D:\sergak dasturi\sergak_smoking\merged\data.yaml")
PROJECT_DIR = Path(r"D:\sergak dasturi\sergak_smoking\runs")
RUN_NAME = "smoking_v8l_640"

# Kaska best.pt - transfer learning starting point
KASKA_BEST_PT = Path(r"D:\sergak dasturi\kaska\runs\helmet_v8l_640\weights\best.pt")

DEFAULTS = {
    "model": "yolov8l.pt",  # Kaska bo'lmasa standart
    "epochs": 100,           # Transfer learning bilan tez konvergensiya
    "imgsz": 640,
    "batch": 6,
    "workers": 4,
    "patience": 25,
    "device": 0,
    "amp": True,
    "cache": False,
    "close_mosaic": 10,
    "optimizer": "AdamW",
    "lr0": 0.001,
    "cos_lr": True,
    "label_smoothing": 0.05,
    "dropout": 0.0,
    "plots": True,
    "save": True,
    "save_period": 10,
    "val": True,
    "verbose": True,
    "exist_ok": True,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=None,
                        help="Boshlangich vazn (default: kaska best.pt yoki yolov8l.pt)")
    parser.add_argument("--epochs", type=int, default=DEFAULTS["epochs"])
    parser.add_argument("--imgsz", type=int, default=DEFAULTS["imgsz"])
    parser.add_argument("--batch", type=int, default=DEFAULTS["batch"])
    parser.add_argument("--workers", type=int, default=DEFAULTS["workers"])
    parser.add_argument("--device", default=DEFAULTS["device"])
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--name", default=RUN_NAME)
    args = parser.parse_args()

    # ultralytics
    try:
        from ultralytics import YOLO
        import torch
    except ImportError:
        print("[X] ultralytics o'rnatilmagan!")
        print("    pip install ultralytics")
        sys.exit(1)

    # data.yaml tekshirish
    if not DATA_YAML.exists():
        print(f"[X] data.yaml topilmadi: {DATA_YAML}")
        print(f"    Avval final_merge_smoking_v2.py ni ishga tushiring")
        sys.exit(1)

    # Model tanlash (transfer learning)
    if args.model is None:
        if KASKA_BEST_PT.exists():
            args.model = str(KASKA_BEST_PT)
            print(f"[+] TRANSFER LEARNING: kaska best.pt dan boshlanmoqda")
            print(f"    {KASKA_BEST_PT}")
        else:
            args.model = "yolov8l.pt"
            print(f"[!] Kaska best.pt topilmadi - YOLOv8l pretrained ishlatamiz")

    print()
    print("=" * 72)
    print("  Sergak AI - SIGARET ANIQLASH TRAINING (1 KLASS)")
    print("=" * 72)
    print(f"  Model:        {args.model}")
    print(f"  Data:         {DATA_YAML}")
    print(f"  Epochs:       {args.epochs}")
    print(f"  Image size:   {args.imgsz}")
    print(f"  Batch:        {args.batch}")
    print(f"  Workers:      {args.workers}")
    print(f"  Device:       {args.device}")
    print(f"  AMP:          {DEFAULTS['amp']}")
    print(f"  Klasslar:     1 (smoking)")
    print(f"  Project:      {PROJECT_DIR}")
    print(f"  Run name:     {args.name}")

    # GPU
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"\n  [GPU] {gpu_name} ({gpu_mem:.1f} GB)")
        print(f"  [PyTorch] {torch.__version__}, CUDA {torch.version.cuda}")
    else:
        print("\n  [!] GPU yo'q - CPU da juda sekin!")
        resp = input("\n  CPU da davom? [y/N]: ")
        if resp.lower() != "y":
            sys.exit(0)
        args.device = "cpu"

    print("\n" + "=" * 72)
    print("  Boshlanmoqda...")
    print("=" * 72 + "\n")

    # Training
    if args.resume:
        last_pt = PROJECT_DIR / args.name / "weights" / "last.pt"
        if not last_pt.exists():
            print(f"[X] Resume uchun last.pt yo'q: {last_pt}")
            sys.exit(1)
        print(f"[+] RESUME: {last_pt}")
        model = YOLO(str(last_pt))
        results = model.train(resume=True)
    else:
        model = YOLO(args.model)

        try:
            results = model.train(
                data=str(DATA_YAML),
                epochs=args.epochs,
                imgsz=args.imgsz,
                batch=args.batch,
                workers=args.workers,
                device=args.device,
                project=str(PROJECT_DIR),
                name=args.name,
                patience=DEFAULTS["patience"],
                amp=DEFAULTS["amp"],
                cache=DEFAULTS["cache"],
                close_mosaic=DEFAULTS["close_mosaic"],
                optimizer=DEFAULTS["optimizer"],
                lr0=DEFAULTS["lr0"],
                cos_lr=DEFAULTS["cos_lr"],
                label_smoothing=DEFAULTS["label_smoothing"],
                plots=DEFAULTS["plots"],
                save=DEFAULTS["save"],
                save_period=DEFAULTS["save_period"],
                val=DEFAULTS["val"],
                verbose=DEFAULTS["verbose"],
                exist_ok=DEFAULTS["exist_ok"],
            )

            print()
            print("=" * 72)
            print("  TRAINING TUGADI!")
            print("=" * 72)
            best = PROJECT_DIR / args.name / "weights" / "best.pt"
            last = PROJECT_DIR / args.name / "weights" / "last.pt"
            print(f"  Eng yaxshi vazn:  {best}")
            print(f"  Oxirgi vazn:      {last}")
            print(f"  Natija papkasi:   {PROJECT_DIR / args.name}")

            # Test split
            print("\n" + "=" * 72)
            print("  TEST SPLIT ustida baholash")
            print("=" * 72)
            metrics = model.val(data=str(DATA_YAML), split="test", imgsz=args.imgsz, batch=args.batch)
            print(f"\n  mAP@0.5:       {metrics.box.map50:.4f}")
            print(f"  mAP@0.5:0.95:  {metrics.box.map:.4f}")
            print(f"  Precision:     {metrics.box.mp:.4f}")
            print(f"  Recall:        {metrics.box.mr:.4f}")

        except torch.cuda.OutOfMemoryError:
            print("\n" + "=" * 72)
            print("  [!] GPU XOTIRA YETMADI")
            print("=" * 72)
            print(f"  Yechim: batch ni kichiklash:")
            print(f"    python scripts/train_smoking.py --batch {args.batch // 2}")
            sys.exit(2)
        except KeyboardInterrupt:
            print("\n\n  [!] Foydalanuvchi to'xtatdi (Ctrl+C)")
            print(f"  Davom ettirish: python scripts/train_smoking.py --resume")
            sys.exit(0)


if __name__ == "__main__":
    main()
