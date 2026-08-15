"""
.pt fayl haqida to'liq ma'lumot olish.
"""
import sys
from pathlib import Path

if len(sys.argv) < 2:
    print("Ishlatish: python check_pt.py <path_to_best.pt>")
    sys.exit(1)

pt_path = Path(sys.argv[1])
if not pt_path.exists():
    print(f"[X] Topilmadi: {pt_path}")
    sys.exit(1)

print()
print("=" * 72)
print(f"  .PT FAYL TAHLILI: {pt_path.name}")
print("=" * 72)
print(f"  Yo'l:    {pt_path}")
print(f"  Hajm:    {pt_path.stat().st_size / 1e6:.1f} MB")
print()

try:
    import torch
    ckpt = torch.load(str(pt_path), map_location="cpu", weights_only=False)
    print(f"  PyTorch: {torch.__version__}")
    print()
except ImportError:
    print("[X] PyTorch yo'q!")
    sys.exit(1)
except Exception as e:
    print(f"[X] Yuklab olish xato: {e}")
    sys.exit(1)

# Asosiy ma'lumotlar
print("=" * 72)
print("  ASOSIY MA'LUMOTLAR")
print("=" * 72)
print(f"  Epoch:           {ckpt.get('epoch', 'noma''lum')}")
print(f"  Best fitness:    {ckpt.get('best_fitness', 'noma''lum')}")
print(f"  Updates:         {ckpt.get('updates', 'noma''lum')}")
print(f"  Date:            {ckpt.get('date', 'noma''lum')}")
print(f"  Version:         {ckpt.get('version', 'noma''lum')}")
print(f"  License:         {ckpt.get('license', 'noma''lum')}")
print()

# Train args
train_args = ckpt.get('train_args', {})
if train_args:
    print("=" * 72)
    print("  TRAINING PARAMETRLARI")
    print("=" * 72)
    for k in ['model', 'data', 'epochs', 'batch', 'imgsz', 'optimizer', 'lr0', 'patience']:
        if k in train_args:
            print(f"  {k:<15s}: {train_args[k]}")
    print()

# Model arxitekturasi
print("=" * 72)
print("  MODEL ARXITEKTURASI")
print("=" * 72)
model = ckpt.get('model', None)
if model:
    try:
        # Param son
        num_params = sum(p.numel() for p in model.parameters() if hasattr(p, 'numel'))
        print(f"  Parametrlar:     {num_params:,}")

        # Class names
        if hasattr(model, 'names') and model.names:
            print(f"  Klasslar soni:   {len(model.names)}")
            print(f"  Klasslar:        {dict(model.names)}")
        elif hasattr(model, 'yaml') and 'nc' in model.yaml:
            print(f"  Klasslar soni:   {model.yaml['nc']}")
    except Exception as e:
        print(f"  [!] Xato: {e}")

# Best metrics
print()
print("=" * 72)
print("  ENG YAXSHI METRIKALAR (best_metrics)")
print("=" * 72)
best_metrics = ckpt.get('best_metrics', {}) or ckpt.get('train_metrics', {}) or {}
if best_metrics:
    for k, v in best_metrics.items():
        if isinstance(v, (int, float)):
            if 'mAP' in k or 'precision' in k.lower() or 'recall' in k.lower():
                print(f"  {k:<30s} {v*100:.2f}%")
            else:
                print(f"  {k:<30s} {v}")
        else:
            print(f"  {k:<30s} {v}")
else:
    print("  [!] best_metrics topilmadi")
    # Boshqa joydan qidirish
    for key in ['metrics', 'train_results', 'val_metrics']:
        if key in ckpt:
            print(f"  {key}: {ckpt[key]}")

# Train results (CSV format)
print()
print("=" * 72)
print("  TRAINING NATIJALARI (oxirgi epoch)")
print("=" * 72)
train_results = ckpt.get('train_results', None)
if train_results:
    try:
        for k, v in list(train_results.items())[:20]:
            print(f"  {k:<30s} {v}")
    except Exception:
        print(f"  {train_results}")

# Class names (alohida)
names = ckpt.get('names', None) or (ckpt.get('train_args', {}).get('names'))
if names:
    print()
    print("=" * 72)
    print("  KLASSLAR")
    print("=" * 72)
    if isinstance(names, dict):
        for k, v in names.items():
            print(f"  [{k}] {v}")
    elif isinstance(names, list):
        for i, n in enumerate(names):
            print(f"  [{i}] {n}")

# Qaror
print()
print("=" * 72)
print("  QAROR")
print("=" * 72)
size_mb = pt_path.stat().st_size / 1e6
arch_guess = "noma'lum"
if size_mb < 10:
    arch_guess = "YOLOv8n (nano) yoki YOLOv5n"
elif size_mb < 30:
    arch_guess = "YOLOv8s (small) yoki YOLOv5s"
elif size_mb < 60:
    arch_guess = "YOLOv8m (medium) yoki stripped YOLOv8l"
elif size_mb < 100:
    arch_guess = "YOLOv8l (stripped) yoki YOLOv8m"
else:
    arch_guess = "YOLOv8l (full)"
print(f"  Arxitektura (taxmin): {arch_guess}")

# Sigaret modelimi yoki kaska?
classes_str = str(ckpt.get('names', '')) + str(names or '')
if 'helmet' in classes_str.lower() or 'hardhat' in classes_str.lower() or 'no_helmet' in classes_str.lower():
    print(f"  Loyiha:               KASKA modeli")
    print(f"  Sigaret training uchun: KO'CHIRISH MUMKIN (transfer learning)")
elif 'smoking' in classes_str.lower() or 'cigarette' in classes_str.lower() or 'smoker' in classes_str.lower():
    print(f"  Loyiha:               SIGARET modeli (allaqachon!)")
elif 'person' in classes_str.lower() and len(str(names)) > 100:
    print(f"  Loyiha:               COCO bazasi (umumiy)")
else:
    print(f"  Loyiha:               aniqlanmadi")

print()
