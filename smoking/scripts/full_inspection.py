"""
SERGAK AI - SIGARET DATASETLAR TO'LIQ TAHLIL
==============================================
Har bir dataset bo'yicha:
  - Klasslar (nomi va soni)
  - Struktura (YOLO / VOC / COCO / FOLDERS)
  - Maqsadga moslashuv (smoking person / cigarette / smoke)
  - Universal class mapping rejasi
  - Tavsiya (USE / TRANSFORM / SKIP)
"""
from pathlib import Path
from collections import Counter, defaultdict
import re
import json

DATASETS_DIR = Path(r"E:\sergak_smoking\datasets")
if not DATASETS_DIR.exists():
    DATASETS_DIR = Path(r"D:\sergak dasturi\smoking\datasets")


# ============================================================
# UNIVERSAL CLASS KARTASI
# ============================================================
# Sergak AI maqsadi: kameradan sigaret chekayotgan odamni aniqlash
# Klasslar:
#   0 = smoking (sigaret chekayotgan / sigaret ko'rinadi)
#   1 = no_smoking (oddiy odam, sigaretsiz)
# Ixtiyoriy:
#   2 = smoke (tutun — sigaret aniqlash uchun emas)

UNIVERSAL_MAPPING = {
    # === SMOKING — sigaret chekayotgan ===
    "smoking": 0, "smoke": 0, "smoker": 0,
    "cigarette": 0, "cigarettes": 0, "cig": 0,
    "cigarrette": 0, "cigerette": 0,
    "vape": 0, "vaping": 0, "vapor": 0,
    "smoking_person": 0, "person_smoking": 0, "smoking-person": 0,
    "head_with_cigarette": 0, "person_with_cigarette": 0,
    "smoking_man": 0, "smoking_woman": 0,
    "ciggarette": 0,
    "tobacco": 0,

    # === NO_SMOKING — chekmagan ===
    "no_smoking": 1, "non-smoking": 1, "non_smoking": 1, "not_smoking": 1,
    "no-smoking": 1, "notsmoking": 1, "notsmoker": 1,
    "no_smoker": 1, "non_smoker": 1, "no-smoker": 1,
    "person": 1, "human": 1, "people": 1,
    "head": 1, "face": 1,
    "no-cigarette": 1, "no_cigarette": 1, "nocigarette": 1,
    "drinking": 1, "drink": 1,  # Boshqa kontekst, sigarret yo'q
    "normal": 1, "no-smoke": 1, "no_smoke": 1,

    # === SMOKE / OTHER ===
    "fire": 2, "flame": 2,  # Olov — sigaret emas
}


def map_class(class_name):
    """Klass nomini universal kartaga moslashtirish."""
    if not class_name:
        return None, "unknown"
    name = class_name.lower().strip().replace(" ", "_")
    if name in UNIVERSAL_MAPPING:
        return UNIVERSAL_MAPPING[name], "exact"
    # Substring qidirish
    for key, val in UNIVERSAL_MAPPING.items():
        if key in name or name in key:
            return val, "substring"
    return None, "unmapped"


def find_classes_yolo(d):
    """data.yaml dan klasslarni o'qish."""
    yamls = list(d.rglob("data.yaml"))
    if not yamls:
        return []
    for yaml_file in yamls:
        try:
            text = yaml_file.read_text(encoding="utf-8", errors="ignore")
            # Format 1: names: [a, b, c]
            m = re.search(r"names\s*:\s*\[([^\]]+)\]", text)
            if m:
                return [n.strip().strip("'\"") for n in m.group(1).split(",")]
            # Format 2: names: \n  - a
            m = re.search(r"names\s*:\s*\n((?:\s*-\s*[^\n]+\n?)+)", text)
            if m:
                return [l.strip().lstrip("-").strip().strip("'\"") for l in m.group(1).split("\n") if l.strip()]
            # Format 3: names:\n  0: a
            pairs = re.findall(r"^\s*(\d+)\s*:\s*['\"]?([^'\"\n]+)['\"]?", text, re.MULTILINE)
            if pairs:
                return [p[1].strip() for p in sorted(pairs, key=lambda x: int(x[0]))]
        except Exception:
            continue
    return []


def count_bboxes_per_class(d, num_classes):
    """YOLO label fayllaridan har bir klassning bbox sonini hisoblash."""
    counter = Counter()
    txts = [f for f in d.rglob("*.txt")
            if f.name not in ("README.txt", "classes.txt", "requirements.txt")]
    for txt in txts[:5000]:  # Performance uchun limit
        try:
            for line in txt.read_text().strip().split("\n"):
                parts = line.split()
                if len(parts) >= 5:
                    try:
                        cls = int(parts[0])
                        if cls < num_classes:
                            counter[cls] += 1
                    except ValueError:
                        pass
        except Exception:
            continue
    return counter


def count_images_per_folder(d):
    """Folder asosidagi datasetlar uchun har bir papkadagi rasmlarni sanash."""
    folder_counts = {}
    for sub in d.iterdir():
        if sub.is_dir():
            imgs = sum(1 for f in sub.rglob("*")
                       if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp"))
            if imgs > 0:
                folder_counts[sub.name] = imgs
    # Va eng ichki papkalarni ham
    for sub in d.iterdir():
        if sub.is_dir():
            for sub2 in sub.iterdir():
                if sub2.is_dir():
                    imgs = sum(1 for f in sub2.rglob("*")
                               if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp"))
                    if imgs > 0 and sub2.name.lower() in [k for k in UNIVERSAL_MAPPING.keys()]:
                        folder_counts[f"{sub.name}/{sub2.name}"] = imgs
    return folder_counts


def detect_format(d):
    """Dataset strukturasini aniqlash."""
    has_yaml = bool(list(d.rglob("data.yaml")))
    has_yolo_txts = sum(1 for f in d.rglob("*.txt") if f.name not in ("README.txt", "classes.txt", "requirements.txt"))
    has_voc_xmls = sum(1 for f in d.rglob("*.xml"))
    has_coco_json = bool(list(d.rglob("_annotations.coco.json")) or list(d.rglob("annotations.json")))
    has_csv = bool(list(d.rglob("*.csv")))
    has_imgs = sum(1 for f in d.rglob("*") if f.suffix.lower() in (".jpg", ".jpeg", ".png"))

    if has_yaml:
        return "YOLO"
    if has_coco_json:
        return "COCO"
    if has_voc_xmls > 10:
        return "VOC"
    if has_yolo_txts > 10:
        return "YOLO (yaml yo'q)"
    if has_csv and has_imgs == 0:
        return "CSV (rasmlar yo'q)"
    # Subdir asosida
    subdirs = [s.name.lower() for s in d.iterdir() if s.is_dir()]
    smoking_keywords = ["smoking", "smoker", "not", "non", "cigarette"]
    if any(kw in s for s in subdirs for kw in smoking_keywords):
        return "FOLDERS"
    return "RAW IMAGES"


def detect_purpose(classes, dataset_name):
    """Datasetning maqsadi: smoking person, cigarette only, smoke?"""
    name_lower = dataset_name.lower()
    classes_lower = [c.lower() for c in classes] if classes else []

    # Tutun fokuslangan
    if any("smoke" in c and "smoking" not in c and "smoker" not in c for c in classes_lower):
        if "smoking" not in classes_lower and "smoker" not in classes_lower:
            if "smoke_kerem" in name_lower or "indoor" in name_lower or "fire" in name_lower:
                return "SMOKE (tutun)", "🟡 Sigaret detection uchun cheklangan foydali"

    # Sigaret object
    if "cigarette" in classes_lower or "cigarettes" in classes_lower:
        if "smoking" not in classes_lower and "person" not in classes_lower:
            return "CIGARETTE (faqat sigaret)", "🟢 Sigaret object detection — IDEAL"

    # Smoking person
    if "smoking" in classes_lower or "smoker" in classes_lower:
        return "SMOKING PERSON", "🟢 Asosiy maqsad — PERFECT"

    # No info
    if not classes:
        if "smoking" in name_lower or "smoker" in name_lower:
            return "SMOKING (taxminiy)", "🟡 Klasslar yo'q, taxminiy"
        if "cigarette" in name_lower or "cig" in name_lower:
            return "CIGARETTE (taxminiy)", "🟡 Klasslar yo'q, taxminiy"
        if "smoke" in name_lower or "fire" in name_lower:
            return "SMOKE/FIRE", "🔴 Sigaret emas"
        return "UNKNOWN", "❓ Tahlil kerak"

    return "MULTI-CLASS", "🟡 Boshqa klasslar bilan aralash"


def main():
    print("=" * 90)
    print("  📊 SERGAK AI - SIGARET DATASETLAR TO'LIQ TAHLIL")
    print(f"  📁 Joylashish: {DATASETS_DIR}")
    print("=" * 90)
    print()

    if not DATASETS_DIR.exists():
        print(f"[X] Papka topilmadi: {DATASETS_DIR}")
        return

    all_datasets = []
    total_imgs = 0

    for d in sorted(DATASETS_DIR.iterdir()):
        if not d.is_dir():
            continue

        # Bosh ma'lumotlar
        imgs = sum(1 for f in d.rglob("*")
                   if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp"))
        if imgs == 0:
            continue

        fmt = detect_format(d)
        classes = find_classes_yolo(d)
        size_mb = sum(f.stat().st_size for f in d.rglob("*") if f.is_file()) / 1e6

        # BBox sanash
        bbox_counts = {}
        if classes and ("YOLO" in fmt):
            counter = count_bboxes_per_class(d, len(classes))
            bbox_counts = {classes[i]: counter[i] for i in range(len(classes))}

        # Folder counts
        folder_counts = {}
        if fmt == "FOLDERS":
            folder_counts = count_images_per_folder(d)

        # Maqsad
        purpose, recommendation = detect_purpose(classes, d.name)

        # Universal mapping
        class_mapping = {}
        unmapped = []
        if classes:
            for i, c in enumerate(classes):
                mapped, match_type = map_class(c)
                if mapped is not None:
                    class_mapping[c] = (mapped, "smoking" if mapped == 0 else "no_smoking" if mapped == 1 else "smoke")
                else:
                    unmapped.append(c)

        all_datasets.append({
            "name": d.name,
            "format": fmt,
            "imgs": imgs,
            "size_mb": size_mb,
            "classes": classes,
            "bbox_counts": bbox_counts,
            "folder_counts": folder_counts,
            "purpose": purpose,
            "recommendation": recommendation,
            "class_mapping": class_mapping,
            "unmapped": unmapped,
        })
        total_imgs += imgs

    # =========================
    # Har bir datasetni chizish
    # =========================
    for ds in all_datasets:
        print()
        print("┌" + "─" * 88 + "┐")
        print(f"│ 📁 {ds['name']:<82s} │")
        print("├" + "─" * 88 + "┤")
        print(f"│ Format:        {ds['format']:<71s} │")
        print(f"│ Rasmlar:       {ds['imgs']:>7,}                                                              │")
        print(f"│ Hajm:          {ds['size_mb']:>7.1f} MB                                                          │")
        print(f"│ Maqsad:        {ds['purpose']:<71s} │")
        print(f"│ Tavsiya:       {ds['recommendation']:<71s} │")

        if ds['classes']:
            print(f"│ Klasslar:      {len(ds['classes'])} ta                                                              │")
            for i, c in enumerate(ds['classes']):
                bbox = ds['bbox_counts'].get(c, 0)
                mapped = ds['class_mapping'].get(c, ("?", "unmapped"))
                arrow = f"-> {mapped[1]} ({mapped[0]})" if mapped[0] != "?" else "-> UNMAPPED"
                print(f"│   [{i}] {c:<25s}  {bbox:>7,} bbox  {arrow:<25s}              │")

        if ds['folder_counts']:
            print(f"│ Papkalar (folder-based):                                                                │")
            for folder, count in ds['folder_counts'].items():
                mapped = map_class(folder)
                m_str = f"-> {'smoking' if mapped[0]==0 else 'no_smoking' if mapped[0]==1 else 'unknown'}"
                print(f"│   {folder:<35s}  {count:>7,} rasm  {m_str:<20s}                  │")

        if ds['unmapped']:
            print(f"│ ⚠️  Mapped emas: {', '.join(ds['unmapped'])[:65]:<71s} │")

        print("└" + "─" * 88 + "┘")

    # =========================
    # Umumiy hisobot
    # =========================
    print()
    print("=" * 90)
    print("  📊 UMUMIY TAHLIL")
    print("=" * 90)
    print(f"  Jami datasetlar: {len(all_datasets)}")
    print(f"  Jami rasmlar:    {total_imgs:,}")
    print()

    # Maqsad bo'yicha guruhlash
    purposes = defaultdict(int)
    for ds in all_datasets:
        purposes[ds['purpose']] += ds['imgs']

    print("  📂 Maqsad bo'yicha:")
    for p, count in sorted(purposes.items(), key=lambda x: -x[1]):
        print(f"     {p:<30s}  {count:>7,} rasm")

    # Tavsiya bo'yicha
    print()
    print("  📋 TAVSIYALAR:")
    use_count = sum(1 for ds in all_datasets if "🟢" in ds['recommendation'])
    transform_count = sum(1 for ds in all_datasets if "🟡" in ds['recommendation'])
    skip_count = sum(1 for ds in all_datasets if "🔴" in ds['recommendation'])
    unknown_count = sum(1 for ds in all_datasets if "❓" in ds['recommendation'])

    print(f"     🟢 IDEAL (to'g'ri ishlatish):       {use_count} dataset")
    print(f"     🟡 SHARTLI (transformatsiya kerak): {transform_count} dataset")
    print(f"     🔴 SKIP (sigaret emas):              {skip_count} dataset")
    print(f"     ❓ TAHLIL KERAK:                     {unknown_count} dataset")

    print()
    print("=" * 90)
    print("  🎯 SERGAK AI MAQSADI:")
    print("=" * 90)
    print()
    print("  Yakuniy 2 klassli model:")
    print("    0 = smoking     (sigaret chekayotgan odam / sigaret bbox)")
    print("    1 = no_smoking  (oddiy odam, sigaretsiz)")
    print()
    print("  Konversiya rejasi:")
    print("    1. 🟢 IDEAL datasetlarni to'g'ridan-to'g'ri ishlatish")
    print("    2. 🟡 SHARTLI larni class mapping bilan transformatsiya")
    print("    3. 🔴 SKIP larni umuman ishlatmaymiz")
    print("    4. ❓ ni qo'lda tekshirish")
    print()


if __name__ == "__main__":
    main()
