"""
Barcha datasetlarni AVTOMATIK topib, 2 klassga (helmet, no_helmet) birlashtirish.

Skript datasets/ papkasidagi har bir subpapkani skanerlaydi, data.yaml dan klasslarni
o'qiydi va aqlli xaritalash bilan birlashtiradi.

Klass xaritalash mantig'i:
  - "helmet", "hat", "hardhat", "with_helmet" → 0 (helmet)
  - "head", "no_helmet", "no-helmet", "without_helmet" → 1 (no_helmet)
  - boshqalari (person, glove, mask, etc.) → SKIP
"""
import random
import re
import shutil
import sys
from pathlib import Path

DATASETS_ROOT = Path(r"D:\sergak dasturi\kaska\datasets")
OUTPUT_DIR = Path(r"D:\sergak dasturi\kaska\merged")
SPLIT_RATIO = {"train": 0.80, "val": 0.15, "test": 0.05}
FINAL_CLASSES = ["helmet", "no_helmet"]
SEED = 42


def classify_class_name(name):
    """Klass nomini olib, bizning 2 klassdan birini qaytarish (yoki None).

    no_helmet (1): "no_helmet", "head", "without_helmet", "no_hardhat", "no_hat", ...
    helmet    (0): "helmet", "hat", "hardhat" (lekin "no" bilan boshlanmasligi kerak)
    None:         person, mask, glove, vehicle, machinery, va h.k.
    """
    n = name.lower().strip().replace("-", "_").replace(" ", "_")
    # Bir nechta underscore'larni bittaga keltirish
    while "__" in n:
        n = n.replace("__", "_")

    # 1. Avval - "no" bilan boshlanadigan helmet variantlari → no_helmet
    if n.startswith("no_") or n.startswith("without_") or n.startswith("non_"):
        # Helmet bilan bog'liqmi tekshirish
        if any(kw in n for kw in ["helmet", "hat", "hardhat", "kaska"]):
            return 1  # no_helmet
        return None  # masalan "no_glove", "no_mask" → skip

    # 2. "head" bu odatda kaskasiz bosh
    if n == "head" or n == "person_head":
        return 1  # no_helmet

    # 3. Sof helmet/hardhat
    if n in ("helmet", "hat", "hardhat", "kaska", "with_helmet", "wearing_helmet"):
        return 0  # helmet
    if "helmet" in n and not any(neg in n for neg in ["no", "without", "non"]):
        return 0
    if "hardhat" in n and not any(neg in n for neg in ["no", "without", "non"]):
        return 0

    # Boshqalari skip
    return None


def read_data_yaml(yaml_path):
    """Oddiy YAML parser - faqat 'names' ni o'qish uchun (kutubxonasiz)."""
    if not yaml_path.exists():
        return None
    text = yaml_path.read_text(encoding="utf-8", errors="ignore")
    names = []
    # Format 1: names: ['a', 'b']
    m = re.search(r"^names\s*:\s*\[([^\]]*)\]", text, re.MULTILINE)
    if m:
        items = m.group(1).split(",")
        names = [it.strip().strip("'\"") for it in items if it.strip()]
        return names
    # Format 2: names:\n  - 'a'\n  - 'b'
    m = re.search(r"^names\s*:\s*\n((?:\s*-\s*['\"]?[^\n]+\n?)+)", text, re.MULTILINE)
    if m:
        for line in m.group(1).split("\n"):
            line = line.strip()
            if line.startswith("-"):
                name = line[1:].strip().strip("'\"")
                if name:
                    names.append(name)
        return names
    # Format 3: names:\n  0: helmet\n  1: no_helmet
    m = re.search(r"^names\s*:\s*\n((?:\s*\d+\s*:\s*[^\n]+\n?)+)", text, re.MULTILINE)
    if m:
        pairs = []
        for line in m.group(1).split("\n"):
            mm = re.match(r"\s*(\d+)\s*:\s*['\"]?([^'\"\n]+)['\"]?", line)
            if mm:
                pairs.append((int(mm.group(1)), mm.group(2).strip()))
        pairs.sort()
        names = [p[1] for p in pairs]
        return names
    return None


# EXPLICIT data.yaml manzillari - auto-discovery ishlamasligi mumkin bo'lganlar uchun
EXPLICIT_YAMLS = [
    DATASETS_ROOT / "kaggle_yolo_helmethead" / "helm" / "helm" / "data.yaml",
    DATASETS_ROOT / "kaggle_hardhat_andrewmvd_yolo" / "data.yaml",
    DATASETS_ROOT / "kaggle_construction_safety" / "css-data" / "data.yaml",
]


def discover_datasets():
    """datasets/ ichidan barcha YOLO formatidagi datasetlarni topish (rekursiv + explicit)."""
    import sys
    found = []
    all_dirs = sorted([d for d in DATASETS_ROOT.iterdir() if d.is_dir()])
    print(f"  Jami papkalar: {len(all_dirs)}\n")

    processed_roots = set()

    # 1. AVVAL — explicit ro'yxat (kafolat bilan topish uchun)
    for yml in EXPLICIT_YAMLS:
        sys.stdout.write(f"  [check] explicit: {yml.relative_to(DATASETS_ROOT)}\n")
        sys.stdout.flush()
        if not yml.exists():
            sys.stdout.write(f"          MAVJUD EMAS\n")
            sys.stdout.flush()
            continue
        root = yml.parent
        names = read_data_yaml(yml)
        if not names:
            sys.stdout.write(f"          klasslar o'qilmadi\n")
            sys.stdout.flush()
            continue
        cmap = {}
        for idx, name in enumerate(names):
            new = classify_class_name(name)
            if new is not None:
                cmap[idx] = new
        if not cmap:
            sys.stdout.write(f"          helmet/no_helmet klass yo'q\n")
            sys.stdout.flush()
            continue
        splits_found = []
        for split in ["train", "valid", "val", "test"]:
            if (root / split / "images").exists():
                splits_found.append(split)
        if not splits_found:
            sys.stdout.write(f"          train/valid/test papkalari yo'q\n")
            sys.stdout.flush()
            continue
        # Bu dataset uchun root papkani belgilash (auto-discovery dublikat qilmasligi uchun)
        ds_name = yml.relative_to(DATASETS_ROOT).parts[0]
        processed_roots.add(ds_name)
        found.append({
            "name": ds_name + "_explicit",
            "root": root,
            "names": names,
            "class_map": cmap,
            "splits": splits_found,
        })
        mapped = {names[k]: ("helmet" if v == 0 else "no_helmet") for k, v in cmap.items()}
        sys.stdout.write(f"  [+] EXPLICIT {ds_name:35s} klasslar: {mapped}\n")
        sys.stdout.flush()

    print()

    # 2. KEYIN — auto-discovery (qolgan datasetlar uchun)
    for d in all_dirs:
        if d.name in processed_roots:
            continue  # explicit ro'yxatdan kelganlarini takror qilish kerak emas
        try:
            yaml_files = sorted(set(d.rglob("data.yaml")))
        except Exception as e:
            print(f"  [err]  {d.name}: {type(e).__name__}: {e}")
            continue
        yaml_files = [y for y in yaml_files
                     if "runs" not in str(y).lower()
                     and "results_yolo" not in str(y).lower()
                     and "args.yaml" not in str(y).lower()]
        if not yaml_files:
            print(f"  [skip] {d.name}: data.yaml topilmadi")
            continue
        # Debug: topilgan barcha yaml'larni ko'rsatish
        if len(yaml_files) > 1:
            print(f"  [info] {d.name}: {len(yaml_files)} ta data.yaml topildi, birinchisi olinadi:")
            for y in yaml_files:
                print(f"         {y.relative_to(DATASETS_ROOT)}")
        for yml in yaml_files:
            root = yml.parent
            names = read_data_yaml(yml)
            if not names:
                continue
            # Klass xaritasi
            cmap = {}
            for idx, name in enumerate(names):
                new = classify_class_name(name)
                if new is not None:
                    cmap[idx] = new
            if not cmap:
                print(f"  [skip] {d.name}: hech qanday helmet/no_helmet klass topilmadi ({names})")
                continue
            # Train/valid/test split papkalarini topish
            splits_found = []
            for split in ["train", "valid", "val", "test"]:
                if (root / split / "images").exists():
                    splits_found.append(split)
            if not splits_found:
                continue
            found.append({
                "name": d.name,
                "root": root,
                "names": names,
                "class_map": cmap,
                "splits": splits_found,
            })
            mapped = {names[k]: ("helmet" if v == 0 else "no_helmet") for k, v in cmap.items()}
            print(f"  [+] {d.name:40s}  klasslar: {mapped}")
            break  # bitta dataset uchun bitta data.yaml yetadi
    return found


def remap_label_file(src, dst, class_map):
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


def collect_pairs(datasets):
    pairs = []
    for ds in datasets:
        ds_count = 0
        for split in ds["splits"]:
            img_dir = ds["root"] / split / "images"
            lbl_dir = ds["root"] / split / "labels"
            if not lbl_dir.exists():
                continue
            for img in img_dir.glob("*"):
                if img.suffix.lower() not in (".jpg", ".jpeg", ".png", ".bmp"):
                    continue
                lbl = lbl_dir / (img.stem + ".txt")
                if not lbl.exists():
                    continue
                pairs.append({
                    "img": img, "lbl": lbl,
                    "ds_name": ds["name"], "class_map": ds["class_map"],
                })
                ds_count += 1
        print(f"    {ds['name']:40s}  {ds_count} ta")
    return pairs


def main():
    print("=" * 70)
    print("  AVTOMATIK datasetlarni topish va 2 klassga birlashtirish")
    print("=" * 70)
    print(f"\n  Skanerlash: {DATASETS_ROOT}\n")

    datasets = discover_datasets()
    if not datasets:
        print("\n[X] Hech qanday yaroqli dataset topilmadi!")
        sys.exit(1)
    print(f"\n  Jami topilgan datasetlar: {len(datasets)}\n")

    print("  Juftliklar yig'ilmoqda...")
    all_pairs = collect_pairs(datasets)
    print(f"\n  JAMI: {len(all_pairs)} ta juftlik")

    random.seed(SEED)
    random.shuffle(all_pairs)

    n = len(all_pairs)
    n_train = int(n * SPLIT_RATIO["train"])
    n_val = int(n * SPLIT_RATIO["val"])
    splits = {
        "train": all_pairs[:n_train],
        "val": all_pairs[n_train:n_train + n_val],
        "test": all_pairs[n_train + n_val:],
    }
    print(f"\n  Taqsimot: train {len(splits['train'])} | val {len(splits['val'])} | test {len(splits['test'])}")

    if OUTPUT_DIR.exists():
        print(f"\n  [!] '{OUTPUT_DIR}' mavjud — tozalanmoqda...")
        shutil.rmtree(OUTPUT_DIR)

    stats = {"helmet": 0, "no_helmet": 0, "skipped": 0}
    for split, items in splits.items():
        img_out = OUTPUT_DIR / "images" / split
        lbl_out = OUTPUT_DIR / "labels" / split
        img_out.mkdir(parents=True, exist_ok=True)
        lbl_out.mkdir(parents=True, exist_ok=True)
        print(f"\n  [{split}] {len(items)} ta...")
        copied = 0
        for i, p in enumerate(items):
            new_name = f"{p['ds_name']}__{p['img'].stem}"
            dst_lbl = lbl_out / (new_name + ".txt")
            if not remap_label_file(p['lbl'], dst_lbl, p['class_map']):
                stats["skipped"] += 1
                continue
            dst_img = img_out / (new_name + p['img'].suffix)
            shutil.copy2(p['img'], dst_img)
            copied += 1
            for line in dst_lbl.read_text().strip().split("\n"):
                cls = int(line.split()[0])
                if cls == 0: stats["helmet"] += 1
                elif cls == 1: stats["no_helmet"] += 1
            if (i + 1) % 3000 == 0:
                print(f"    {i+1}/{len(items)}")
        print(f"  [OK] {copied} ta yozildi")

    yaml_content = f"""# Sergak AI - Kaska aniqlash (avtomatik birlashtirilgan)
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
    print("\n" + "=" * 70)
    print("  YAKUN")
    print("=" * 70)
    print(f"\n  Joylashish: {OUTPUT_DIR}")
    print(f"\n  Bbox statistikasi:")
    if total > 0:
        print(f"    helmet:    {stats['helmet']:>7} ({stats['helmet']*100//total}%)")
        print(f"    no_helmet: {stats['no_helmet']:>7} ({stats['no_helmet']*100//total}%)")
        print(f"    JAMI:      {total:>7}")
    print(f"  O'tkazib yuborilgan: {stats['skipped']}")


if __name__ == "__main__":
    main()
