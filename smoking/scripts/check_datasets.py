"""
Sigaret datasetlarning strukturasini tekshirish.
Kaska loyihasidagi check_datasets.py ning sigaret versiyasi.
"""
from pathlib import Path
import re

DATASETS_ROOT = Path(r"E:\sergak_smoking\datasets")


def detect_format(d):
    """Dataset formatini aniqlash."""
    yamls = list(d.glob("**/data.yaml"))
    if yamls:
        return "YOLO", yamls[0]
    if (d / "annotations").exists() or list(d.glob("**/annotations")):
        return "VOC", None
    xmls = list(d.glob("**/*.xml"))
    if len(xmls) > 10:
        return "VOC-XML", None
    # COCO format
    cocos = list(d.glob("**/_annotations.coco.json"))
    if cocos or list(d.glob("**/annotations.json")):
        return "COCO", None
    return "Unknown", None


def count_items(d):
    """Rasm va label fayllarni sanash."""
    imgs = sum(1 for f in d.rglob("*") if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp"))
    txts = sum(1 for f in d.rglob("*.txt") if f.name not in ("README.txt", "classes.txt"))
    xmls = sum(1 for f in d.rglob("*.xml"))
    return imgs, txts, xmls


def read_classes(yaml_path):
    """data.yaml dan klasslarni o'qish."""
    if not yaml_path or not yaml_path.exists():
        return []
    text = yaml_path.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"names\s*:\s*\[([^\]]+)\]", text)
    if m:
        return [n.strip().strip("'\"") for n in m.group(1).split(",") if n.strip()]
    m = re.search(r"names\s*:\s*\n((?:\s*-\s*[^\n]+\n?)+)", text)
    if m:
        return [l.strip().lstrip("-").strip().strip("'\"") for l in m.group(1).split("\n") if l.strip()]
    pairs = re.findall(r"^\s*(\d+)\s*:\s*['\"]?([^'\"\n]+)['\"]?", text, re.MULTILINE)
    if pairs:
        return [p[1].strip() for p in sorted(pairs, key=lambda x: int(x[0]))]
    return []


def main():
    print("=" * 80)
    print(f"  Sigaret Datasetlar Diagnostikasi: {DATASETS_ROOT}")
    print("=" * 80)
    print()

    if not DATASETS_ROOT.exists():
        print(f"[X] Papka mavjud emas: {DATASETS_ROOT}")
        print(f"    Avval datasetlarni yuklab oling va E:\\sergak_smoking\\datasets\\ ga qo'ying")
        return

    total_imgs = 0
    total_ready = 0

    for d in sorted(DATASETS_ROOT.iterdir()):
        if not d.is_dir():
            continue
        if d.name.startswith("."):
            continue
        if not list(d.iterdir()):
            continue

        fmt, yaml = detect_format(d)
        imgs, txts, xmls = count_items(d)
        classes = read_classes(yaml) if yaml else []

        print(f"\n[{fmt}] {d.name}")
        print(f"  Rasmlar:    {imgs:>6,}")
        print(f"  YOLO .txt:  {txts:>6,}")
        print(f"  VOC .xml:   {xmls:>6,}")
        if classes:
            print(f"  Klasslar:   {classes}")

        total_imgs += imgs
        if fmt == "YOLO" and txts > 0:
            total_ready += imgs

    print()
    print("=" * 80)
    print(f"  JAMI rasmlar: {total_imgs:,}")
    print(f"  YOLO formatida tayyor: {total_ready:,}")
    print(f"  Konversiya kerak: ~{total_imgs - total_ready:,}")
    print("=" * 80)


if __name__ == "__main__":
    main()
