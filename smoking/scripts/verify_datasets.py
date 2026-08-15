"""
Datasetlarni TO'LIQ tekshirish — qayerda nima saqlanganini ko'rish.
"""
from pathlib import Path
import sys

PROJECT_ROOT = Path(r"E:\sergak_smoking")
DATASETS_DIR = PROJECT_ROOT / "datasets"
# Agar E:\ yo'q bo'lsa D:\ ga qarash
if not Path("E:\\").exists():
    PROJECT_ROOT = Path(r"D:\sergak dasturi\smoking")
    DATASETS_DIR = PROJECT_ROOT / "datasets"

print("=" * 72)
print(f"  Datasetlar tekshiruvi: {DATASETS_DIR}")
print("=" * 72)

if not DATASETS_DIR.exists():
    print(f"\n[X] Papka yo'q: {DATASETS_DIR}")
    sys.exit(1)

total_images = 0
total_labels = 0
total_size = 0

for d in sorted(DATASETS_DIR.iterdir()):
    if not d.is_dir():
        continue

    print()
    print(f"📁 {d.name}")
    print(f"   Yo'l: {d}")

    # Barcha rasm va label fayllarni topish (rekursiv)
    imgs = []
    txts = []
    yamls = []
    xmls = []
    jsons = []
    size = 0

    for f in d.rglob("*"):
        if not f.is_file():
            continue
        size += f.stat().st_size
        ext = f.suffix.lower()
        if ext in (".jpg", ".jpeg", ".png", ".bmp", ".webp"):
            imgs.append(f)
        elif ext == ".txt":
            txts.append(f)
        elif ext in (".yaml", ".yml"):
            yamls.append(f)
        elif ext == ".xml":
            xmls.append(f)
        elif ext == ".json":
            jsons.append(f)

    total_images += len(imgs)
    total_labels += len(txts)
    total_size += size

    print(f"   Rasmlar:     {len(imgs):>5,}")
    print(f"   YOLO .txt:   {len(txts):>5,}")
    print(f"   data.yaml:   {len(yamls):>5,}")
    print(f"   VOC .xml:    {len(xmls):>5,}")
    print(f"   JSON:        {len(jsons):>5,}")
    print(f"   Hajm:        {size/1e6:.1f} MB")

    # Eng birinchi ichki struktura ko'rinishi
    if imgs:
        print(f"   1-rasm:     {imgs[0].relative_to(d)}")
    if yamls:
        print(f"   1-yaml:     {yamls[0].relative_to(d)}")
        # Klasslarni o'qish
        try:
            text = yamls[0].read_text(encoding="utf-8", errors="ignore")
            # Klasslarni topish
            import re
            m = re.search(r"names\s*:\s*\[([^\]]+)\]", text)
            if m:
                classes = [n.strip().strip("'\"") for n in m.group(1).split(",")]
                print(f"   Klasslar:   {classes}")
            else:
                m = re.search(r"names\s*:\s*\n((?:\s*-\s*[^\n]+\n?)+)", text)
                if m:
                    classes = [l.strip().lstrip("-").strip().strip("'\"") for l in m.group(1).split("\n") if l.strip()]
                    print(f"   Klasslar:   {classes}")
                else:
                    pairs = re.findall(r"^\s*(\d+)\s*:\s*['\"]?([^'\"\n]+)['\"]?", text, re.MULTILINE)
                    if pairs:
                        classes = [p[1].strip() for p in sorted(pairs, key=lambda x: int(x[0]))]
                        print(f"   Klasslar:   {classes}")
        except Exception:
            pass

    # Ichki papkalarni ko'rsatish (faqat birinchi daraja)
    subdirs = sorted([s.name for s in d.iterdir() if s.is_dir()])
    if subdirs:
        print(f"   Ichki papkalar: {subdirs[:5]}")

print()
print("=" * 72)
print("  UMUMIY")
print("=" * 72)
print(f"  Jami papka:  {sum(1 for d in DATASETS_DIR.iterdir() if d.is_dir())}")
print(f"  Jami rasm:   {total_images:,}")
print(f"  Jami label:  {total_labels:,}")
print(f"  Jami hajm:   {total_size/1e9:.2f} GB")
print()
