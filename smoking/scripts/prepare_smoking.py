"""
SERGAK AI - SIGARET DATASETLAR KONVERSIYA
==========================================
Hamma datasetlarni 2 klassli YOLO formatga keltirish:
  0 = smoking (sigaret chekayotgan / sigaret object)
  1 = no_smoking (oddiy odam, sigaretsiz)

Folder-based datasetlar uchun:
  - Folder smoking/cigarette/smoker  -> butun rasm = bbox (class 0)
  - Folder not_smoking/normal         -> butun rasm = bbox (class 1)

Manzil: E:\\sergak_smoking\\prepared\\
"""
from pathlib import Path
import shutil
import re

DATASETS_DIR = Path(r"E:\sergak_smoking\datasets")
PREPARED_DIR = Path(r"E:\sergak_smoking\prepared")

if not Path("E:\\").exists():
    DATASETS_DIR = Path(r"D:\sergak dasturi\smoking\datasets")
    PREPARED_DIR = Path(r"D:\sergak dasturi\smoking\prepared")


def log(msg, lvl="INFO"):
    symbols = {"INFO": "[i]", "OK": "[+]", "WARN": "[!]", "ERR": "[X]",
               "SKIP": "[-]", "PROCESS": "[→]"}
    print(f"  {symbols.get(lvl, '[?]')} {msg}")


def header(title):
    print()
    print("=" * 72)
    print(f"  {title}")
    print("=" * 72)


# ============================================================
# UNIVERSAL CLASS MAPPING
# ============================================================
SMOKING_KEYWORDS = ["smoking", "smoker", "cigarette", "cigarettes", "cig",
                    "cigarrette", "ciggarette", "tobacco", "vape", "vaping"]
NO_SMOKING_KEYWORDS = ["not_smoking", "non_smoking", "non-smoking", "no_smoking",
                       "no-smoking", "notsmoking", "not", "non", "no_smoker",
                       "non_smoker", "normal", "drinking", "drink"]


def classify_folder(folder_name):
    """Folder nomidan klass aniqlash."""
    name = folder_name.lower().strip()
    # Aniq matchlar
    for kw in NO_SMOKING_KEYWORDS:
        if kw == name or kw in name.split("_") or kw in name.split("-"):
            return 1  # no_smoking
    for kw in SMOKING_KEYWORDS:
        if kw == name:
            return 0  # smoking
    # Substring qidirish (smoking ham smoke_xxx ga to'g'ri kelmasin)
    if any(kw in name for kw in NO_SMOKING_KEYWORDS):
        return 1
    if any(kw in name for kw in SMOKING_KEYWORDS):
        return 0
    return None


def copy_image_with_label(src_img, dst_img, label_content):
    """Rasm va label faylini ko'chirish."""
    dst_img.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(src_img), str(dst_img))

    label_path = dst_img.parent.parent / "labels" / (dst_img.stem + ".txt")
    label_path.parent.mkdir(parents=True, exist_ok=True)
    label_path.write_text(label_content)


# ============================================================
# DATASET KONFIGURATSIYALARI
# ============================================================
DATASETS_CONFIG = [
    # === FOLDER-BASED (smoking/not_smoking papkalar) ===
    {
        "name": "kgl_cigarette_smoker_dataset",
        "type": "folder",
        "expected": 9004,
    },
    # === FILENAME-BASED (notsmoking_*.jpg / smoking_*.jpg) ===
    {
        "name": "mnd_smoker_detection",
        "type": "filename",  # notsmoking_*.jpg -> 1, boshqasi -> 0
        "expected": 1120,
    },
    {
        "name": "mnd_smoking_not_smoking",
        "type": "filename",  # notsmoking_*.jpg -> 1, boshqasi -> 0
        "expected": 2410,
    },
    {
        "name": "mnd_cigdet",
        "type": "filename",  # smoking_*.jpg -> 0
        "expected": 557,
        "default_class": 0,
    },
    # === YOLO format (data.yaml + labels) ===
    {
        "name": "kgl_smoking_and_drinking_dataset_for_yolo",
        "type": "yolo",
        "class_map": {0: None, 1: 0},  # 0=drinking->skip, 1=smoking->0
        "expected": 1030,
    },
    {
        "name": "gh_smoking_meera",
        "type": "yolo",
        "class_map": {0: 0},  # Smoking->0
        "expected": 9,
    },
    # === SKIPPED (smoke/fire detection, not cigarette) ===
    # hf_smoke_kerem, znd_indoor_smoke, gh_smoke_* skip
]


def classify_filename(filename):
    """Fayl nomidan klassni aniqlash (mnd datasetlar uchun)."""
    name = filename.lower()
    # NOT smoking signallari
    if name.startswith("notsmoking") or name.startswith("not_smoking") or \
       name.startswith("non_smoking") or name.startswith("nonsmoking"):
        return 1  # no_smoking
    # smoking signallari
    if name.startswith("smoking") or name.startswith("smoker") or \
       name.startswith("cigarette") or name.startswith("cig"):
        return 0  # smoking
    # Abc/aa/aagg patternlari — odatda smoking (mnd datasetlarda)
    if re.match(r"^(abc|aa|aagg|ii)\d+", name):
        return 0  # smoking
    return None


def process_filename_dataset(ds_dir, output_name, default_class=None):
    """Fayl nomi bo'yicha klass aniqlash."""
    log(f"Filename-based: {output_name}", "PROCESS")
    output_dir = PREPARED_DIR / output_name
    if output_dir.exists():
        shutil.rmtree(output_dir)

    counts = {"smoking": 0, "no_smoking": 0, "skipped": 0}

    for img_path in ds_dir.rglob("*"):
        if not img_path.is_file():
            continue
        if img_path.suffix.lower() not in (".jpg", ".jpeg", ".png", ".bmp"):
            continue

        cls = classify_filename(img_path.name)
        if cls is None and default_class is not None:
            cls = default_class
        if cls is None:
            counts["skipped"] += 1
            continue

        label_content = f"{cls} 0.5 0.5 1.0 1.0"
        new_name = f"{output_name}__{img_path.stem}{img_path.suffix}"
        dst_img = output_dir / "images" / new_name
        copy_image_with_label(img_path, dst_img, label_content)

        if cls == 0:
            counts["smoking"] += 1
        else:
            counts["no_smoking"] += 1

    log(f"smoking: {counts['smoking']:,}, no_smoking: {counts['no_smoking']:,}, skip: {counts['skipped']:,}", "OK")
    return counts


# ============================================================
# 1) FOLDER-BASED DATASETLARNI KONVERTATSIYA
# ============================================================
def process_folder_dataset(ds_dir, output_name):
    """Folder asosidagi datasetni butun-rasm bbox bilan YOLO ga konvertatsiya."""
    log(f"Folder-based: {output_name}", "PROCESS")
    output_dir = PREPARED_DIR / output_name
    if output_dir.exists():
        shutil.rmtree(output_dir)

    counts = {"smoking": 0, "no_smoking": 0, "skipped": 0}

    # Hamma JPG/PNG fayllarni topish
    for img_path in ds_dir.rglob("*"):
        if not img_path.is_file():
            continue
        if img_path.suffix.lower() not in (".jpg", ".jpeg", ".png", ".bmp", ".webp"):
            continue

        # Rasmning yo'lidagi papka nomlaridan klassni aniqlash
        cls = None
        for parent in img_path.parents:
            if parent == ds_dir or parent == ds_dir.parent:
                break
            c = classify_folder(parent.name)
            if c is not None:
                cls = c
                break

        if cls is None:
            counts["skipped"] += 1
            continue

        # YOLO format: butun rasm = bbox (cx=0.5, cy=0.5, w=1.0, h=1.0)
        label_content = f"{cls} 0.5 0.5 1.0 1.0"

        # Yangi nom (datasetga noyob)
        new_name = f"{output_name}__{img_path.stem}{img_path.suffix}"
        dst_img = output_dir / "images" / new_name
        copy_image_with_label(img_path, dst_img, label_content)

        if cls == 0:
            counts["smoking"] += 1
        else:
            counts["no_smoking"] += 1

    log(f"smoking: {counts['smoking']:,}, no_smoking: {counts['no_smoking']:,}, skip: {counts['skipped']:,}", "OK")
    return counts


# ============================================================
# 2) YOLO FORMAT (data.yaml bilan)
# ============================================================
def process_yolo_dataset(ds_dir, output_name, class_map):
    """YOLO format datasetni class mapping bilan konvertatsiya."""
    log(f"YOLO: {output_name}", "PROCESS")
    output_dir = PREPARED_DIR / output_name
    if output_dir.exists():
        shutil.rmtree(output_dir)

    counts = {"smoking": 0, "no_smoking": 0, "skipped": 0}

    # Hamma label fayllarini topish
    label_files = list(ds_dir.rglob("*.txt"))
    label_files = [f for f in label_files
                   if f.name not in ("README.txt", "classes.txt", "requirements.txt")]

    for label_path in label_files:
        try:
            content = label_path.read_text().strip()
            if not content:
                continue

            new_lines = []
            for line in content.split("\n"):
                parts = line.strip().split()
                if len(parts) != 5:
                    continue
                try:
                    old_cls = int(parts[0])
                    new_cls = class_map.get(old_cls)
                    if new_cls is None:
                        continue  # skip qilingan klass
                    new_lines.append(f"{new_cls} {parts[1]} {parts[2]} {parts[3]} {parts[4]}")
                    if new_cls == 0:
                        counts["smoking"] += 1
                    elif new_cls == 1:
                        counts["no_smoking"] += 1
                except (ValueError, IndexError):
                    continue

            if not new_lines:
                counts["skipped"] += 1
                continue

            # Rasm faylini topish (.txt o'rniga .jpg/.png/.jpeg)
            img_found = None
            for ext in (".jpg", ".jpeg", ".png", ".bmp"):
                # Avval .txt yo'lining yonidagi rasmni qidirish
                candidate = label_path.parent / (label_path.stem + ext)
                if candidate.exists():
                    img_found = candidate
                    break
                # /labels/ -> /images/ ga almashtirish
                if "labels" in label_path.parts:
                    img_alt = Path(str(label_path).replace("\\labels\\", "\\images\\").replace("/labels/", "/images/"))
                    img_alt = img_alt.with_suffix(ext)
                    if img_alt.exists():
                        img_found = img_alt
                        break

            if not img_found:
                counts["skipped"] += 1
                continue

            new_name = f"{output_name}__{img_found.stem}{img_found.suffix}"
            dst_img = output_dir / "images" / new_name
            copy_image_with_label(img_found, dst_img, "\n".join(new_lines))
        except Exception as e:
            counts["skipped"] += 1
            continue

    log(f"smoking: {counts['smoking']:,} bbox, no_smoking: {counts['no_smoking']:,} bbox, skip: {counts['skipped']:,}", "OK")
    return counts


# ============================================================
# 3) YOLO format yaml siz (mnd_cigdet)
# ============================================================
def process_yolo_no_yaml(ds_dir, output_name, default_class=0):
    """YOLO labels bor lekin data.yaml yo'q — barchasini bir klassga."""
    log(f"YOLO (no yaml): {output_name} -> class {default_class}", "PROCESS")
    output_dir = PREPARED_DIR / output_name
    if output_dir.exists():
        shutil.rmtree(output_dir)

    counts = {"smoking": 0, "no_smoking": 0, "skipped": 0}

    label_files = list(ds_dir.rglob("*.txt"))
    label_files = [f for f in label_files
                   if f.name not in ("README.txt", "classes.txt", "requirements.txt")]

    for label_path in label_files:
        try:
            content = label_path.read_text().strip()
            if not content:
                continue

            new_lines = []
            for line in content.split("\n"):
                parts = line.strip().split()
                if len(parts) != 5:
                    continue
                try:
                    # Default class ga moslashtirish
                    float(parts[1])  # tekshirish
                    new_lines.append(f"{default_class} {parts[1]} {parts[2]} {parts[3]} {parts[4]}")
                    if default_class == 0:
                        counts["smoking"] += 1
                    else:
                        counts["no_smoking"] += 1
                except (ValueError, IndexError):
                    continue

            if not new_lines:
                continue

            # Rasm topish
            img_found = None
            for ext in (".jpg", ".jpeg", ".png", ".bmp"):
                candidate = label_path.parent / (label_path.stem + ext)
                if candidate.exists():
                    img_found = candidate
                    break

            if not img_found:
                counts["skipped"] += 1
                continue

            new_name = f"{output_name}__{img_found.stem}{img_found.suffix}"
            dst_img = output_dir / "images" / new_name
            copy_image_with_label(img_found, dst_img, "\n".join(new_lines))
        except Exception:
            counts["skipped"] += 1
            continue

    log(f"smoking: {counts['smoking']:,} bbox, skip: {counts['skipped']:,}", "OK")
    return counts


# ============================================================
# MAIN
# ============================================================
def main():
    print()
    print("=" * 72)
    print("  🚀 SERGAK AI - SIGARET DATASETLAR KONVERSIYA")
    print("=" * 72)
    print(f"  Kirish:  {DATASETS_DIR}")
    print(f"  Chiqish: {PREPARED_DIR}")
    print()

    PREPARED_DIR.mkdir(parents=True, exist_ok=True)

    grand_counts = {"smoking": 0, "no_smoking": 0, "skipped": 0}
    processed_datasets = []

    for ds_cfg in DATASETS_CONFIG:
        ds_dir = DATASETS_DIR / ds_cfg["name"]
        if not ds_dir.exists():
            log(f"YO'Q: {ds_cfg['name']}", "SKIP")
            continue

        header(ds_cfg["name"])

        try:
            if ds_cfg["type"] == "folder":
                counts = process_folder_dataset(ds_dir, ds_cfg["name"])
            elif ds_cfg["type"] == "yolo":
                counts = process_yolo_dataset(ds_dir, ds_cfg["name"], ds_cfg["class_map"])
            elif ds_cfg["type"] == "yolo_no_yaml":
                counts = process_yolo_no_yaml(ds_dir, ds_cfg["name"], ds_cfg.get("default_class", 0))
            elif ds_cfg["type"] == "filename":
                counts = process_filename_dataset(ds_dir, ds_cfg["name"], ds_cfg.get("default_class"))
            else:
                continue

            for k, v in counts.items():
                grand_counts[k] += v
            processed_datasets.append((ds_cfg["name"], counts))
        except Exception as e:
            log(f"Xato: {e}", "ERR")

    # YAKUNIY HISOBOT
    header("📊 YAKUNIY KONVERSIYA HISOBOTI")
    print(f"  Konvertatsiya qilingan datasetlar: {len(processed_datasets)}")
    print()
    print("  Har bir dataset:")
    for name, counts in processed_datasets:
        total = counts['smoking'] + counts['no_smoking']
        print(f"    {name:<45s}  smoking={counts['smoking']:>5,}  no_smoking={counts['no_smoking']:>5,}  JAMI={total:>5,}")
    print()
    print("  YAKUN:")
    print(f"    🔴 smoking (0):     {grand_counts['smoking']:>6,} rasm/bbox")
    print(f"    🟢 no_smoking (1):  {grand_counts['no_smoking']:>6,} rasm/bbox")
    print(f"    ⚪ skipped:         {grand_counts['skipped']:>6,}")
    print(f"    ────────────────────────────────")
    print(f"    📊 JAMI:            {grand_counts['smoking'] + grand_counts['no_smoking']:>6,} rasm/bbox")
    print()
    print(f"  📁 Joylashish: {PREPARED_DIR}")
    print()
    print("  KEYINGI QADAM:")
    print("    python scripts/final_merge_smoking.py  (yoki .bat orqali)")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] To'xtatildi")
    except Exception as e:
        print(f"\n[X] FATAL XATO: {e}")
        import traceback
        traceback.print_exc()
