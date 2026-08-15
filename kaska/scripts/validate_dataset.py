"""Yakuniy mergedan oldin dataset to'liq tekshiruvi."""
from pathlib import Path
from collections import Counter

root = Path(r"D:\sergak dasturi\kaska\merged")
per_split = {}
total = 0
total_bbox = 0
class_count = Counter()
ds_count = Counter()

for split in ["train", "val", "test"]:
    imgs_dir = root / "images" / split
    lbls_dir = root / "labels" / split
    img_files = list(imgs_dir.iterdir())
    lbl_files = list(lbls_dir.iterdir())
    img_stems = {p.stem for p in img_files if p.is_file()}
    lbl_stems = {p.stem for p in lbl_files if p.is_file()}
    only_img = img_stems - lbl_stems
    only_lbl = lbl_stems - img_stems
    split_bbox = 0
    split_classes = Counter()
    empty_labels = 0
    bad_class = 0
    bad_coords = 0
    bad_format = 0
    suspicious_tiny = 0  # juda kichik bbox

    for p in lbl_files:
        if not p.is_file():
            continue
        try:
            content = p.read_text().strip()
        except Exception:
            continue
        if not content:
            empty_labels += 1
            continue
        for line in content.split("\n"):
            parts = line.strip().split()
            if len(parts) != 5:
                bad_format += 1
                continue
            try:
                cls = int(parts[0])
                cx, cy, w, h = map(float, parts[1:5])
            except ValueError:
                bad_format += 1
                continue
            if cls not in (0, 1):
                bad_class += 1
                continue
            if not (0 <= cx <= 1 and 0 <= cy <= 1 and 0 < w <= 1 and 0 < h <= 1):
                bad_coords += 1
                continue
            if w < 0.005 or h < 0.005:
                suspicious_tiny += 1
            split_classes[cls] += 1
            split_bbox += 1

    # Manba dataset bo'yicha sanash
    for p in img_files:
        if "__" in p.name:
            ds_count[p.name.split("__")[0]] += 1

    per_split[split] = {
        "imgs": len(img_stems),
        "lbls": len(lbl_stems),
        "orphan_img": len(only_img),
        "orphan_lbl": len(only_lbl),
        "empty_lbl": empty_labels,
        "bad_format": bad_format,
        "bad_class": bad_class,
        "bad_coords": bad_coords,
        "suspicious_tiny": suspicious_tiny,
        "bbox": split_bbox,
        "helmet": split_classes[0],
        "no_helmet": split_classes[1],
    }
    total += len(img_stems)
    total_bbox += split_bbox
    class_count.update(split_classes)

print("=" * 70)
print("  HAR BIR SPLIT NATIJASI")
print("=" * 70)
for split, d in per_split.items():
    print(f"\n[{split.upper()}]")
    print(f"  Rasm: {d['imgs']:,}   Label: {d['lbls']:,}")
    print(f"  Labelsiz rasm: {d['orphan_img']}  |  Rasmsiz label: {d['orphan_lbl']}")
    print(f"  Bo'sh label: {d['empty_lbl']}  |  Format xato: {d['bad_format']}")
    print(f"  Noto'g'ri klass: {d['bad_class']}  |  Koordinata xato: {d['bad_coords']}")
    print(f"  Juda kichik bbox (<0.5%): {d['suspicious_tiny']}")
    print(f"  Bbox: {d['bbox']:,}  (helmet={d['helmet']:,}, no_helmet={d['no_helmet']:,})")
    if d['bbox'] > 0:
        h_pct = d['helmet'] * 100 / d['bbox']
        print(f"  Balans: helmet {h_pct:.1f}% / no_helmet {100-h_pct:.1f}%")

print()
print("=" * 70)
print("  UMUMIY HOLAT")
print("=" * 70)
print(f"  Jami rasm: {total:,}")
print(f"  Jami bbox: {total_bbox:,}")
print(f"  O'rtacha bbox/rasm: {total_bbox/total:.1f}")
print(f"  helmet: {class_count[0]:,} ({class_count[0]*100/total_bbox:.1f}%)")
print(f"  no_helmet: {class_count[1]:,} ({class_count[1]*100/total_bbox:.1f}%)")

print()
print("=" * 70)
print("  MANBA DATASET TAQSIMOTI")
print("=" * 70)
for ds, n in sorted(ds_count.items(), key=lambda x: -x[1]):
    print(f"  {ds:25s} {n:>7,} ({n*100/total:.1f}%)")

print()
print("=" * 70)
print("  TRAINING TAYYORLIK YAKUNI")
print("=" * 70)
all_ok = True
checks = []

# Har bir check
def check(name, cond, detail=""):
    global all_ok
    symbol = "[OK]" if cond else "[XATO]"
    if not cond:
        all_ok = False
    checks.append((symbol, name, detail))
    return cond

check("data.yaml mavjud", (root/"data.yaml").exists())
check("train rasmlar va labellar teng", per_split["train"]["imgs"] == per_split["train"]["lbls"])
check("val rasmlar va labellar teng", per_split["val"]["imgs"] == per_split["val"]["lbls"])
check("test rasmlar va labellar teng", per_split["test"]["imgs"] == per_split["test"]["lbls"])
check("labelsiz rasm yo'q", sum(d["orphan_img"] for d in per_split.values()) == 0)
check("rasmsiz label yo'q", sum(d["orphan_lbl"] for d in per_split.values()) == 0)
check("format xato yo'q", sum(d["bad_format"] for d in per_split.values()) == 0)
check("noto'g'ri klass yo'q", sum(d["bad_class"] for d in per_split.values()) == 0)
check("koordinata xato yo'q", sum(d["bad_coords"] for d in per_split.values()) == 0)
check("bo'sh label kam", sum(d["empty_lbl"] for d in per_split.values()) < total * 0.05)
check("train >= 50000", per_split["train"]["imgs"] >= 50000)
check("klass balansi 20-80% oraliqda",
      0.20 < class_count[0]/total_bbox < 0.80)

for symbol, name, detail in checks:
    print(f"  {symbol} {name}")

print()
print("=" * 70)
if all_ok:
    print("  [OK] DATASET TRAININGGA TO'LIQ TAYYOR!")
else:
    print("  [!] BA'ZI MUAMMOLAR BOR — yuqorida ko'rsatilgan")
print("=" * 70)
