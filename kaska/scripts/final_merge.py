"""
YAKUNIY MERGE - 2 ta YOLO strukturasini ham qo'llab-quvvatlaydi:
  A) root/<split>/images/  +  root/<split>/labels/    (Joseph stili)
  B) root/images/<split>/  +  root/labels/<split>/    (Helmethead stili)
"""
import random
import re
import shutil
import sys
from pathlib import Path

DATASETS_ROOT = Path(r"D:\sergak dasturi\kaska\datasets")
OUTPUT_DIR = Path(r"D:\sergak dasturi\kaska\merged")
SPLIT_RATIO = {"train": 0.80, "val": 0.15, "test": 0.05}
SEED = 42

# EXPLICIT DATASET KONFIGURATSIYASI - har birini qo'lda belgilaymiz
# Bu ishonchli — auto-discovery ishlamaganda ham xato bo'lmaydi
DATASETS = [
    {
        "name": "joseph_hardhat",
        "root": DATASETS_ROOT / "roboflow_joseph_hardhat" / "Hard-Hat-Workers-2",
        "structure": "A",  # root/<split>/images/
        "classes": ["head", "helmet", "person"],
        "class_map": {0: 1, 1: 0, 2: None},  # head->no_helmet, helmet->helmet, person->skip
        "splits": ["train", "test"],
    },
    {
        "name": "ppe",
        "root": DATASETS_ROOT / "roboflow_ppe" / "PPEs-4",
        "structure": "A",
        "classes": ["glove", "goggles", "helmet", "mask", "no-suit", "no_glove",
                   "no_goggles", "no_helmet", "no_mask", "no_shoes", "shoes", "suit"],
        "class_map": {2: 0, 7: 1},  # faqat helmet va no_helmet
        "splits": ["train", "valid"],
    },
    {
        "name": "helmet_tracking",
        "root": DATASETS_ROOT / "helmet-tracking-2" / "helmet-tracking-2",
        "structure": "A",
        "classes": ["helmet", "no-helmet"],
        "class_map": {0: 0, 1: 1},
        "splits": ["train", "valid", "test"],
    },
    {
        "name": "construction_safety",
        "root": DATASETS_ROOT / "kaggle_construction_safety" / "css-data",
        "structure": "A",
        "classes": ["Hardhat", "Mask", "NO-Hardhat", "NO-Mask", "NO-Safety Vest",
                   "Person", "Safety Cone", "Safety Vest", "machinery", "vehicle"],
        "class_map": {0: 0, 2: 1},  # Hardhat->helmet, NO-Hardhat->no_helmet
        "splits": ["train", "valid", "test"],
    },
    {
        "name": "andrewmvd_yolo",
        "root": DATASETS_ROOT / "kaggle_hardhat_andrewmvd_yolo",
        "structure": "B",  # root/images/<split>/  ← TESKARI!
        "classes": ["helmet", "no_helmet"],
        "class_map": {0: 0, 1: 1},
        "splits": ["train", "valid"],
    },
    {
        "name": "yolo_helmethead",
        "root": DATASETS_ROOT / "kaggle_yolo_helmethead" / "helm" / "helm",
        "structure": "B",  # root/images/<split>/  ← TESKARI!
        "classes": ["head", "helmet"],
        "class_map": {0: 1, 1: 0},  # head->no_helmet, helmet->helmet
        "splits": ["train", "valid", "test"],
    },
    # ===== YANGI 3 TA DATASET (2026-05-25) =====
    {
        "name": "shel5k",
        "root": DATASETS_ROOT / "shel5k_yolo",
        "structure": "B",  # root/images/<split>/
        "classes": ["helmet", "no_helmet"],  # allaqachon 2 klassga konvertatsiya qilingan
        "class_map": {0: 0, 1: 1},
        "splits": ["train", "valid"],
    },
    {
        "name": "gdut_hwd",
        "root": DATASETS_ROOT / "gdut_hwd_yolo",
        "structure": "B",  # root/images/<split>/
        "classes": ["helmet", "no_helmet"],  # white/yellow/red/blue->helmet, none->no_helmet
        "class_map": {0: 0, 1: 1},
        "splits": ["train", "valid"],
    },
    {
        "name": "shwd",
        "root": DATASETS_ROOT / "shwd_yolo",
        "structure": "B",  # root/images/<split>/
        "classes": ["helmet", "no_helmet"],  # hat->helmet, person->no_helmet
        "class_map": {0: 0, 1: 1},
        "splits": ["train", "valid", "test"],
    },
    {
        "name": "sh17",
        "root": DATASETS_ROOT / "sh17_yolo",
        "structure": "B",  # root/images/<split>/
        "classes": ["helmet", "no_helmet"],  # helmet bbox + head (IoU filtrlangan)
        "class_map": {0: 0, 1: 1},
        "splits": ["train", "valid"],
    },
]


def get_split_paths(ds, split):
    """Struktura turiga qarab images va labels papkalari yo'lini qaytarish."""
    root = ds["root"]
    if ds["structure"] == "A":
        # root/<split>/images/ + root/<split>/labels/
        return root / split / "images", root / split / "labels"
    elif ds["structure"] == "B":
        # root/images/<split>/ + root/labels/<split>/
        return root / "images" / split, root / "labels" / split
    return None, None


def remap_label(src, dst, class_map):
    """Label fayl o'qish va klasslarni qayta xaritalash."""
    if not src.exists():
        return False
    new_lines = []
    try:
        for line in src.read_text(encoding="utf-8", errors="ignore").strip().split("\n"):
            parts = line.strip().split()
            if len(parts) < 5:
                continue
            old = int(parts[0])
            new = class_map.get(old)
            if new is None:
                continue
            new_lines.append(f"{new} {parts[1]} {parts[2]} {parts[3]} {parts[4]}")
    except Exception:
        return False
    if not new_lines:
        return False
    dst.write_text("\n".join(new_lines))
    return True


def collect_all_pairs():
    """Barcha datasetlardan rasm+label juftliklarini yig'ish."""
    pairs = []
    print("=" * 70)
    print("  Datasetlarni skanerlash")
    print("=" * 70)

    for ds in DATASETS:
        print(f"\n  [+] {ds['name']:25s} ({ds['structure']}-stil)")
        print(f"      root: {ds['root'].relative_to(DATASETS_ROOT)}")
        if not ds["root"].exists():
            print(f"      [X] PAPKA MAVJUD EMAS - o'tkaziladi")
            continue
        ds_count = 0
        for split in ds["splits"]:
            img_dir, lbl_dir = get_split_paths(ds, split)
            if not img_dir.exists() or not lbl_dir.exists():
                print(f"      [-] {split}: papka yo'q")
                continue
            split_count = 0
            for img in img_dir.glob("*"):
                if img.suffix.lower() not in (".jpg", ".jpeg", ".png", ".bmp"):
                    continue
                lbl = lbl_dir / (img.stem + ".txt")
                if not lbl.exists():
                    continue
                pairs.append({
                    "img": img, "lbl": lbl,
                    "ds_name": ds["name"],
                    "class_map": ds["class_map"],
                })
                split_count += 1
            ds_count += split_count
            print(f"      [+] {split}: {split_count:>6,} ta")
        print(f"      JAMI: {ds_count:,} ta")
    return pairs


def main():
    pairs = collect_all_pairs()
    n = len(pairs)
    print()
    print("=" * 70)
    print(f"  UMUMIY JAMI: {n:,} ta rasm-label juftligi")
    print("=" * 70)

    if n == 0:
        print("[X] Hech narsa topilmadi!")
        sys.exit(1)

    # Aralashtirish
    random.seed(SEED)
    random.shuffle(pairs)

    # Bo'lish
    n_train = int(n * SPLIT_RATIO["train"])
    n_val = int(n * SPLIT_RATIO["val"])
    splits = {
        "train": pairs[:n_train],
        "val": pairs[n_train:n_train + n_val],
        "test": pairs[n_train + n_val:],
    }
    print(f"\n  Taqsimot:")
    print(f"    train: {len(splits['train']):,}")
    print(f"    val:   {len(splits['val']):,}")
    print(f"    test:  {len(splits['test']):,}")

    # Tozalash
    if OUTPUT_DIR.exists():
        print(f"\n  [!] Eski merged tozalanmoqda...")
        shutil.rmtree(OUTPUT_DIR)

    # Ko'chirish
    stats = {"helmet": 0, "no_helmet": 0, "skipped": 0}
    print()
    print("=" * 70)
    print("  Birlashtirilmoqda...")
    print("=" * 70)
    for split_name, items in splits.items():
        img_out = OUTPUT_DIR / "images" / split_name
        lbl_out = OUTPUT_DIR / "labels" / split_name
        img_out.mkdir(parents=True, exist_ok=True)
        lbl_out.mkdir(parents=True, exist_ok=True)
        print(f"\n  [{split_name}] {len(items):,} ta ko'chirilmoqda...")
        copied = 0
        for i, p in enumerate(items):
            new_name = f"{p['ds_name']}__{p['img'].stem}"
            dst_lbl = lbl_out / (new_name + ".txt")
            if not remap_label(p['lbl'], dst_lbl, p['class_map']):
                stats["skipped"] += 1
                continue
            dst_img = img_out / (new_name + p['img'].suffix)
            shutil.copy2(p['img'], dst_img)
            copied += 1
            for line in dst_lbl.read_text().strip().split("\n"):
                cls = int(line.split()[0])
                if cls == 0: stats["helmet"] += 1
                elif cls == 1: stats["no_helmet"] += 1
            if (i + 1) % 5000 == 0:
                print(f"    {i+1:,}/{len(items):,}")
        print(f"  [OK] {copied:,} ta yozildi")

    # data.yaml
    yaml_content = f"""# Sergak AI - Kaska aniqlash YAKUNIY dataset
path: {OUTPUT_DIR.as_posix()}
train: images/train
val: images/val
test: images/test

nc: 2
names:
  0: helmet
  1: no_helmet
"""
    (OUTPUT_DIR / "data.yaml").write_text(yaml_content, encoding="utf-8")

    total = stats["helmet"] + stats["no_helmet"]
    print()
    print("=" * 70)
    print("  YAKUNIY NATIJA")
    print("=" * 70)
    print(f"  Joylashish: {OUTPUT_DIR}")
    print(f"\n  Bbox statistikasi:")
    if total > 0:
        print(f"    helmet:    {stats['helmet']:>8,} ({stats['helmet']*100//total}%)")
        print(f"    no_helmet: {stats['no_helmet']:>8,} ({stats['no_helmet']*100//total}%)")
        print(f"    JAMI:      {total:>8,}")
    print(f"  O'tkazib yuborilgan: {stats['skipped']:,}")


if __name__ == "__main__":
    main()
