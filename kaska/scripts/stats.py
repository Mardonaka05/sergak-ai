"""
Dataset statistikasi: necha rasm, har klassdan necha bounding box, balans.

ISHLATISH:
    python stats.py <dataset_path>

Misol:
    python stats.py "D:\\sergak dasturi\\kaska\\merged"
"""
import sys
from pathlib import Path
from collections import Counter, defaultdict


def analyze(dataset_dir):
    dataset_dir = Path(dataset_dir)
    print("=" * 60)
    print(f"  Dataset tahlili: {dataset_dir.name}")
    print("=" * 60)

    splits = ["train", "val", "test"]
    for split in splits:
        img_dir = dataset_dir / "images" / split
        lbl_dir = dataset_dir / "labels" / split
        if not img_dir.exists():
            continue

        images = list(img_dir.glob("*"))
        images = [i for i in images if i.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp")]
        labels = list(lbl_dir.glob("*.txt")) if lbl_dir.exists() else []

        class_counts = Counter()
        empty_labels = 0
        total_boxes = 0

        for lbl_file in labels:
            try:
                content = lbl_file.read_text().strip()
                if not content:
                    empty_labels += 1
                    continue
                for line in content.split("\n"):
                    parts = line.strip().split()
                    if len(parts) >= 1:
                        cls_id = int(parts[0])
                        class_counts[cls_id] += 1
                        total_boxes += 1
            except Exception as e:
                continue

        print(f"\n  [{split.upper()}]")
        print(f"    Rasmlar:        {len(images)}")
        print(f"    Labellar:       {len(labels)}")
        print(f"    Bo'sh labellar: {empty_labels}")
        print(f"    Jami bbox:      {total_boxes}")
        for cls_id, count in sorted(class_counts.items()):
            name = "helmet" if cls_id == 0 else ("no_helmet" if cls_id == 1 else f"class_{cls_id}")
            pct = 100 * count / total_boxes if total_boxes else 0
            print(f"    Klass {cls_id} ({name}): {count} ({pct:.1f}%)")

    print("\n" + "=" * 60)
    print("  Balans tavsiya:")
    print("    - Har klass kamida 30% bo'lishi yaxshi")
    print("    - Agar bir klass 80%+ bo'lsa, model 'noto'g'ri' o'rganadi")
    print("    - Yechim: kam klassdan ko'proq rasm yig'ing")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Ishlatish: python stats.py <dataset_path>")
        sys.exit(1)
    analyze(sys.argv[1])
