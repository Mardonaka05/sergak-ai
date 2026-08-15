"""
SERGAK AI - SIGARET DATASETLAR KONVERSIYA (v3 - FAQAT 1 KLASS)
==================================================================
6 ta TOZA SIGARET datasetni 1-klassli YOLO formatga keltirish:
  0 = smoking (sigaret chekayotgan / sigaret object)

no_smoking klassi YO'Q — model faqat smoking ni topadi.
Sergak AI uchun:
  - smoking bbox topilsa -> ALARM
  - bbox topilmasa -> OK
"""
from pathlib import Path
import shutil
import re
import yaml

DATASETS_DIR = Path(r"D:\sergak dasturi\sergak_smoking\datasets")
PREPARED_DIR = Path(r"D:\sergak dasturi\sergak_smoking\prepared")


def log(msg, lvl="INFO"):
    symbols = {"INFO": "[i]", "OK": "[+]", "WARN": "[!]", "ERR": "[X]",
               "SKIP": "[-]", "PROC": "[->"}
    print(f"  {symbols.get(lvl, '[?]')} {msg}")


def header(title):
    print()
    print("=" * 72)
    print(f"  {title}")
    print("=" * 72)


def parse_yaml_classes(yaml_path):
    """data.yaml dan klasslarni o'qish."""
    try:
        text = yaml_path.read_text(encoding="utf-8", errors="ignore")
        # Format 1: names: [a, b]
        m = re.search(r"names\s*:\s*\[([^\]]+)\]", text)
        if m:
            return [n.strip().strip("'\"") for n in m.group(1).split(",")]
        # Format 2: names:\n  - a\n  - b
        m = re.search(r"names\s*:\s*\n((?:\s*-\s*[^\n]+\n?)+)", text)
        if m:
            return [l.strip().lstrip("-").strip().strip("'\"")
                    for l in m.group(1).split("\n") if l.strip()]
        # Format 3: names:\n  0: a
        pairs = re.findall(r"^\s*(\d+)\s*:\s*['\"]?([^'\"\n]+?)['\"]?\s*$",
                            text, re.MULTILINE)
        if pairs:
            return [p[1].strip() for p in sorted(pairs, key=lambda x: int(x[0]))]
    except Exception:
        pass
    return []


# ============================================================
# UNIVERSAL CLASS MAPPING — FAQAT 1 KLASS (smoking = 0)
# ============================================================
def universal_class_map(class_name):
    """Klass nomidan universal mapping qaytaradi.
    smoking/cigarette -> 0
    boshqa hamma narsa -> None (SKIP)"""
    if not class_name:
        return None
    n = class_name.lower().strip().replace("-", "_").replace(" ", "_")

    # Avval no_smoking ekanligini tekshirish (negative bo'lmasin)
    no_smoking_keys = ["no_smoking", "non_smoking", "not_smoking", "nosmoking",
                       "no_smoker", "non_smoker", "notsmoker", "nonsmoker",
                       "no_cigarette", "no_cig"]
    if any(k == n for k in no_smoking_keys):
        return None  # SKIP - no_smoking ni qabul qilmaymiz
    if any(neg in n for neg in ["no_", "not_", "non_", "no-", "not-", "non-"]):
        return None  # SKIP - negative

    # 0 = SMOKING (sigaret bilan)
    smoking_keys = ["smoking", "smoker", "cigarette", "cigarettes", "cig",
                    "cigarrette", "ciggarette", "tobacco", "person_smoking",
                    "smoking_person", "head_with_cigarette", "person_with_cigarette",
                    "smoking_man", "smoking_woman", "smk"]
    if n in smoking_keys:
        return 0
    if any(k == n.split("_")[0] for k in smoking_keys):
        return 0
    if any(k in n for k in smoking_keys):
        return 0

    return None  # mapped emas - skip


def find_image_for_label(label_path, ds_root):
    """Label fayl uchun mos rasmni topish."""
    stem = label_path.stem
    # Labels va images papkalari odatda yonma-yon
    candidates = []

    # 1. /labels/X.txt -> /images/X.jpg
    if "labels" in label_path.parts:
        path_str = str(label_path)
        for ext in (".jpg", ".jpeg", ".png", ".bmp"):
            img_alt = Path(path_str.replace("\\labels\\", "\\images\\").replace("/labels/", "/images/"))
            img_alt = img_alt.with_suffix(ext)
            if img_alt.exists():
                return img_alt

    # 2. Yonida
    for ext in (".jpg", ".jpeg", ".png", ".bmp"):
        cand = label_path.parent / (stem + ext)
        if cand.exists():
            return cand

    return None


# ============================================================
# YOLO Roboflow datasetlarni konvertatsiya
# ============================================================
def process_yolo_roboflow(ds_dir, output_name):
    """Roboflow YOLO formatdagi datasetni 2-klassli formatga keltirish."""
    log(f"YOLO Roboflow: {output_name}", "PROC")

    # data.yaml topish
    yamls = list(ds_dir.rglob("data.yaml"))
    if not yamls:
        log(f"data.yaml topilmadi", "ERR")
        return None

    classes = parse_yaml_classes(yamls[0])
    if not classes:
        log(f"Klasslar o'qib olinmadi", "ERR")
        return None

    log(f"Original klasslar: {classes}", "INFO")

    # Class mapping (faqat smoking = 0, qolganlari SKIP)
    class_map = {}
    for i, c in enumerate(classes):
        mapped = universal_class_map(c)
        class_map[i] = mapped
        if mapped == 0:
            log(f"  [{i}] {c} -> smoking (0)", "OK")
        else:
            log(f"  [{i}] {c} -> SKIP", "WARN")

    # Output papka
    output_dir = PREPARED_DIR / output_name
    if output_dir.exists():
        shutil.rmtree(output_dir)
    (output_dir / "images").mkdir(parents=True, exist_ok=True)
    (output_dir / "labels").mkdir(parents=True, exist_ok=True)

    # Label fayllarini topish
    label_files = []
    for sub in ["train", "valid", "test"]:
        labels_dir = None
        for d in ds_dir.rglob(f"{sub}/labels"):
            if d.is_dir():
                labels_dir = d
                break
        if labels_dir:
            label_files.extend([(f, sub) for f in labels_dir.glob("*.txt")
                                if f.name not in ("classes.txt",)])

    # Agar split bo'lmasa - barchasini topish
    if not label_files:
        for txt in ds_dir.rglob("*.txt"):
            if txt.name in ("README.txt", "classes.txt", "requirements.txt"):
                continue
            label_files.append((txt, "all"))

    counts = {"smoking": 0, "skipped_bbox": 0, "skipped_imgs": 0}
    processed = 0

    for label_path, split in label_files:
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
                    if new_cls != 0:  # faqat smoking saqlanadi
                        counts["skipped_bbox"] += 1
                        continue
                    # smoking = 0 yagona klass
                    new_lines.append(f"0 {parts[1]} {parts[2]} {parts[3]} {parts[4]}")
                    counts["smoking"] += 1
                except (ValueError, IndexError):
                    continue

            if not new_lines:
                counts["skipped_imgs"] += 1
                continue

            # Rasmni topish
            img = find_image_for_label(label_path, ds_dir)
            if not img:
                counts["skipped_imgs"] += 1
                continue

            # Yangi nom
            new_stem = f"{output_name}__{split}__{img.stem}"
            dst_img = output_dir / "images" / f"{new_stem}{img.suffix}"
            dst_lbl = output_dir / "labels" / f"{new_stem}.txt"

            shutil.copy2(str(img), str(dst_img))
            dst_lbl.write_text("\n".join(new_lines))
            processed += 1
        except Exception:
            continue

    log(f"  Yozildi: {processed:,} rasm", "OK")
    log(f"  smoking bbox: {counts['smoking']:,}", "INFO")
    log(f"  skip bbox: {counts['skipped_bbox']:,}", "INFO")
    log(f"  skip rasm: {counts['skipped_imgs']:,}", "INFO")
    return counts


# ============================================================
# DATASETLAR RO'YXATI
# ============================================================
DATASETS_TO_PROCESS = [
    "rbf_archive",
    "rbf_final_smoking_v3",
    "rbf_smoking_people_v2",
    "rbf_smoking_smoker1",
    "rbf_smoking_v1",
    "Smoking-CCTV-Detection_v1",
]


def main():
    print()
    print("=" * 72)
    print("  SERGAK AI - SIGARET DATASETLAR KONVERSIYA v3 (1 KLASS)")
    print("=" * 72)
    print(f"  Kirish:  {DATASETS_DIR}")
    print(f"  Chiqish: {PREPARED_DIR}")
    print()
    print("  Konvertatsiya rejasi (FAQAT 1 KLASS):")
    print("    0 = smoking  (sigaret chekayotgan odam / sigaret bbox)")
    print()

    PREPARED_DIR.mkdir(parents=True, exist_ok=True)

    grand_counts = {"smoking": 0, "skipped_bbox": 0, "skipped_imgs": 0}
    processed_count = 0

    for ds_name in DATASETS_TO_PROCESS:
        ds_dir = DATASETS_DIR / ds_name
        if not ds_dir.exists():
            log(f"YO'Q: {ds_name}", "SKIP")
            continue

        header(ds_name)
        counts = process_yolo_roboflow(ds_dir, ds_name)
        if counts:
            for k, v in counts.items():
                grand_counts[k] += v
            processed_count += 1

    # YAKUNIY HISOBOT
    header("YAKUNIY HISOBOT")
    print(f"  Konvertatsiya qilindi: {processed_count} dataset")
    print()
    print(f"  🔴 smoking bbox jami:     {grand_counts['smoking']:>7,}")
    print(f"  skip bbox (no_smoking + boshqalar): {grand_counts['skipped_bbox']:>7,}")
    print(f"  skip rasm (smoking yo'q): {grand_counts['skipped_imgs']:>7,}")
    print()

    # Yakuniy papkadagi rasmlarni sanash
    total_imgs = 0
    for d in PREPARED_DIR.iterdir():
        if d.is_dir():
            imgs_dir = d / "images"
            if imgs_dir.exists():
                n = sum(1 for f in imgs_dir.iterdir()
                        if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp"))
                total_imgs += n
                print(f"  {d.name:<40s}  {n:>7,} rasm")

    print()
    print(f"  📊 JAMI TAYYORLANGAN: {total_imgs:,} rasm")
    print()
    print(f"  📁 {PREPARED_DIR}")
    print()
    print("=" * 72)
    print("  KEYINGI QADAM:")
    print("=" * 72)
    print()
    print("    final_merge_smoking.py — 80/15/5 train/val/test split")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] To'xtatildi")
    except Exception as e:
        print(f"\n[X] XATO: {e}")
        import traceback
        traceback.print_exc()
