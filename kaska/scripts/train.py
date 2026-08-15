"""
Sergak AI - Kaska aniqlash modeli treningi.

Default:
  Model:   YOLOv8l (eng yaxshi 2-klassli kaska aniqlash uchun)
  Image:   640 (RTX 3060/4060/8GB GPU uchun moslangan)
  Batch:   6 (AMP bilan 8GB ga sig'adi)
  Epochs:  150
  AMP:     YOQ (mixed precision - 40% xotira tejash)
  Resume:  agar oxirgi run bo'lsa, davom etadi

Ishga tushirish:
  python scripts/train.py
  python scripts/train.py --resume   # uzilgan o'qishni davom ettirish
  python scripts/train.py --model yolov8m.pt --batch 8  # boshqa model
"""
import argparse
import sys
from pathlib import Path

# ---- Konfiguratsiya ----
DATA_YAML = Path(r"D:\sergak dasturi\kaska\merged\data.yaml")
PROJECT_DIR = Path(r"D:\sergak dasturi\kaska\runs")
RUN_NAME = "helmet_v8l_640"

DEFAULTS = {
    "model": "yolov8l.pt",
    "epochs": 150,
    "imgsz": 640,
    "batch": 6,           # 8GB GPU uchun xavfsiz
    "workers": 4,
    "patience": 30,       # 30 epoch yaxshilanishsiz - to'xtatish
    "device": 0,          # birinchi GPU
    "amp": True,          # MUHIM: xotira 40% tejash
    "cache": False,       # RAM tejash uchun yo'q
    "close_mosaic": 10,   # oxirgi 10 epoch mosaic o'chirilsin
    "optimizer": "AdamW",
    "lr0": 0.001,         # AdamW past lr ni yaxshi ko'radi
    "cos_lr": True,       # cosine LR scheduler
    "label_smoothing": 0.05,
    "dropout": 0.0,
    "plots": True,
    "save": True,
    "save_period": 10,    # har 10 epoch da checkpoint
    "val": True,
    "verbose": True,
    "exist_ok": True,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=DEFAULTS["model"])
    parser.add_argument("--epochs", type=int, default=DEFAULTS["epochs"])
    parser.add_argument("--imgsz", type=int, default=DEFAULTS["imgsz"])
    parser.add_argument("--batch", type=int, default=DEFAULTS["batch"])
    parser.add_argument("--workers", type=int, default=DEFAULTS["workers"])
    parser.add_argument("--device", default=DEFAULTS["device"])
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--name", default=RUN_NAME)
    args = parser.parse_args()

    # ultralytics borligini tekshirish
    try:
        from ultralytics import YOLO
        import torch
    except ImportError:
        print("[X] ultralytics o'rnatilmagan!")
        print("    pip install ultralytics")
        sys.exit(1)

    # data.yaml borligini tekshirish
    if not DATA_YAML.exists():
        print(f"[X] data.yaml topilmadi: {DATA_YAML}")
        sys.exit(1)

    print("=" * 70)
    print("  Sergak AI - Kaska aniqlash treningi")
    print("=" * 70)
    print(f"  Model:        {args.model}")
    print(f"  Data:         {DATA_YAML}")
    print(f"  Epochs:       {args.epochs}")
    print(f"  Image size:   {args.imgsz}")
    print(f"  Batch:        {args.batch}")
    print(f"  Workers:      {args.workers}")
    print(f"  Device:       {args.device}")
    print(f"  AMP:          {DEFAULTS['amp']}")
    print(f"  Project:      {PROJECT_DIR}")
    print(f"  Run name:     {args.name}")

    # GPU ma'lumotlari
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"\n  [GPU] {gpu_name} ({gpu_mem:.1f} GB)")
        print(f"  [PyTorch] {torch.__version__}, CUDA {torch.version.cuda}")
    else:
        print("\n  [!] GPU topilmadi - CPU da ishlaydi (juda sekin!)")
        if args.device != "cpu":
            resp = input("\n  CPU da davom etamizmi? (yo'q deyish tavsiya etiladi) [y/N]: ")
            if resp.lower() != "y":
                sys.exit(0)
            args.device = "cpu"

    print("\n" + "=" * 70)
    print("  Boshlanmoqda...")
    print("=" * 70 + "\n")

    # RESUME — last.pt dan davom ettirish
    if args.resume:
        last_pt = PROJECT_DIR / args.name / "weights" / "last.pt"
        if not last_pt.exists():
            print(f"[X] Resume uchun last.pt topilmadi: {last_pt}")
            print("    Yangi training boshlash uchun --resume olib tashlang.")
            sys.exit(1)
        print(f"[+] RESUME: {last_pt}")
        model = YOLO(str(last_pt))
        # Resume holatida hammasini last.pt dan o'qiydi (faqat resume=True yetadi)
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
            resume=args.resume,
        )

        print()
        print("=" * 70)
        print("  TRAINING TUGADI!")
        print("=" * 70)
        best = PROJECT_DIR / args.name / "weights" / "best.pt"
        last = PROJECT_DIR / args.name / "weights" / "last.pt"
        print(f"  Eng yaxshi vazn:  {best}")
        print(f"  Oxirgi vazn:      {last}")
        print(f"  Natija papkasi:   {PROJECT_DIR / args.name}")

        # Test ustida baholash
        print("\n" + "=" * 70)
        print("  TEST SPLIT ustida baholash")
        print("=" * 70)
        metrics = model.val(data=str(DATA_YAML), split="test", imgsz=args.imgsz, batch=args.batch)
        print(f"\n  mAP@0.5:       {metrics.box.map50:.4f}")
        print(f"  mAP@0.5:0.95:  {metrics.box.map:.4f}")
        print(f"  Precision:     {metrics.box.mp:.4f}")
        print(f"  Recall:        {metrics.box.mr:.4f}")

    except torch.cuda.OutOfMemoryError:
        print("\n" + "=" * 70)
        print("  [!] GPU XOTIRA YETMADI (OutOfMemoryError)")
        print("=" * 70)
        print(f"  Hozirgi batch: {args.batch}")
        print(f"  Yechim: batch ni kichiklash:")
        print(f"    python scripts/train.py --batch {args.batch // 2}")
        print(f"  Yoki kichikroq model:")
        print(f"    python scripts/train.py --model yolov8m.pt")
        sys.exit(2)
    except KeyboardInterrupt:
        print("\n\n  [!] Foydalanuvchi to'xtatdi (Ctrl+C)")
        print(f"  Davom ettirish: python scripts/train.py --resume")
        sys.exit(0)


if __name__ == "__main__":
    main()
