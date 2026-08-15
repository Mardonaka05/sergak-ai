"""
SERGAK AI - SIGARET DATASETLARNI TAHLIL QILISH
================================================
Har bir datasetning strukturasi, formati, klasslarini ko'rish.
Konversiya skriptini yozishdan oldin to'liq tahlil.
"""
from pathlib import Path
import re

DATASETS_DIR = Path(r"E:\sergak_smoking\datasets")
if not DATASETS_DIR.exists():
    DATASETS_DIR = Path(r"D:\sergak dasturi\smoking\datasets")


def find_classes_yolo(d):
    """data.yaml dan klasslarni o'qish."""
    yamls = list(d.rglob("data.yaml"))
    if not yamls:
        return []
    try:
        text = yamls[0].read_text(encoding="utf-8", errors="ignore")
        # Format 1: names: [a, b, c]
        m = re.search(r"names\s*:\s*\[([^\]]+)\]", text)
        if m:
            return [n.strip().strip("'\"") for n in m.group(1).split(",")]
        # Format 2: names: \n  - a\n  - b
        m = re.search(r"names\s*:\s*\n((?:\s*-\s*[^\n]+\n?)+)", text)
        if m:
            return [l.strip().lstrip("-").strip().strip("'\"") for l in m.group(1).split("\n") if l.strip()]
        # Format 3: names:\n  0: a\n  1: b
        pairs = re.findall(r"^\s*(\d+)\s*:\s*['\"]?([^'\"\n]+)['\"]?", text, re.MULTILINE)
        if pairs:
            return [p[1].strip() for p in sorted(pairs, key=lambda x: int(x[0]))]
    except Exception:
        pass
    return []


def detect_structure(d):
    """Dataset strukturasini aniqlash."""
    # 1. YOLO: data.yaml + images/ + labels/
    if list(d.rglob("data.yaml")):
        return "YOLO"
    # 2. Subfoldered: papka nomlari (smoking/, not_smoking/)
    subdirs = [s for s in d.iterdir() if s.is_dir()]
    if any("smok" in s.name.lower() or "cig" in s.name.lower() for s in subdirs):
        return "FOLDERS"
    # 3. COCO
    if list(d.rglob("_annotations.coco.json")) or list(d.rglob("annotations.json")):
        return "COCO"
    # 4. VOC
    if list(d.rglob("Annotations")) or any(s.name.lower() in ("voc2007", "voc2012") for s in subdirs):
        return "VOC"
    # 5. CSV/Sensor
    if list(d.rglob("*.csv")) and not list(d.rglob("*.jpg")):
        return "CSV"
    return "UNKNOWN"


def main():
    print("=" * 80)
    print(f"  SIGARET DATASETLARNI TAHLIL QILISH")
    print(f"  Joylashish: {DATASETS_DIR}")
    print("=" * 80)
    print()

    if not DATASETS_DIR.exists():
        print(f"[X] Papka topilmadi: {DATASETS_DIR}")
        return

    total_imgs = 0
    datasets_info = []

    for d in sorted(DATASETS_DIR.iterdir()):
        if not d.is_dir():
            continue

        print()
        print(f"📁 {d.name}")
        print("-" * 80)
        print(f"   Yo'l: {d}")

        # Struktura aniqlash
        structure = detect_structure(d)
        print(f"   Struktura: {structure}")

        # Rasmlar/labellar/yaml/xml
        imgs = list(d.rglob("*.jpg")) + list(d.rglob("*.jpeg")) + list(d.rglob("*.png")) + list(d.rglob("*.bmp"))
        txts = [f for f in d.rglob("*.txt") if f.name not in ("README.txt", "classes.txt")]
        xmls = list(d.rglob("*.xml"))
        yamls = list(d.rglob("data.yaml"))
        csvs = list(d.rglob("*.csv"))
        jsons = list(d.rglob("*.json"))

        print(f"   Rasmlar:     {len(imgs):>7,}")
        print(f"   YOLO .txt:   {len(txts):>7,}")
        print(f"   VOC .xml:    {len(xmls):>7,}")
        print(f"   data.yaml:   {len(yamls):>7,}")
        print(f"   CSV/JSON:    {len(csvs)}/{len(jsons)}")

        # Klasslar
        classes = find_classes_yolo(d)
        if classes:
            print(f"   Klasslar:    {classes}")

        # Ichki struktura (birinchi 5 papkalar)
        subdirs = sorted([s.name for s in d.iterdir() if s.is_dir()])[:8]
        if subdirs:
            print(f"   Ichki:       {', '.join(subdirs)}")

        # Hajm
        size_mb = sum(f.stat().st_size for f in d.rglob("*") if f.is_file()) / 1e6
        print(f"   Hajm:        {size_mb:.1f} MB")

        # 1-rasm va 1-label namuna
        if imgs:
            print(f"   1-rasm:      {imgs[0].relative_to(d)}")
        if txts:
            print(f"   1-label:     {txts[0].relative_to(d)}")
            try:
                content = txts[0].read_text().strip().split("\n")[:3]
                print(f"   Label namuna: {content}")
            except Exception:
                pass

        total_imgs += len(imgs)
        datasets_info.append({
            "name": d.name,
            "structure": structure,
            "imgs": len(imgs),
            "classes": classes,
            "txts": len(txts),
            "xmls": len(xmls),
        })

    print()
    print("=" * 80)
    print("  UMUMIY")
    print("=" * 80)
    print(f"  Datasetlar:  {len(datasets_info)}")
    print(f"  JAMI rasm:   {total_imgs:,}")
    print()
    print("=" * 80)
    print("  KONVERSIYA REJASI")
    print("=" * 80)
    for ds in datasets_info:
        action = ""
        if ds["structure"] == "YOLO":
            action = "Class mapping kerak"
        elif ds["structure"] == "FOLDERS":
            action = "Folder->bbox auto-label kerak"
        elif ds["structure"] == "VOC":
            action = "VOC->YOLO konversiya"
        elif ds["structure"] == "COCO":
            action = "COCO->YOLO konversiya"
        elif ds["structure"] == "CSV":
            action = "SKIP (CSV sensor data, rasm yo'q)"
        else:
            action = "Tekshirish kerak"
        print(f"  {ds['name']:<45s}  {ds['structure']:<10s}  -> {action}")
    print()


if __name__ == "__main__":
    main()
