"""
Bounding box'larni rasmlar ustiga chizib ko'rish.
Dataset to'g'ri annotatsiyalanganini tekshirish uchun.

ISHLATISH:
    python visualize.py <dataset_path> [split=train] [count=10]

Misol:
    python visualize.py "D:\\sergak dasturi\\kaska\\merged" train 20
"""
import sys
import random
from pathlib import Path

try:
    import cv2
except ImportError:
    print("[!] OpenCV o'rnatilmagan: pip install opencv-python")
    sys.exit(1)

CLASS_COLORS = {
    0: (0, 200, 0),     # helmet - yashil
    1: (0, 0, 255),     # no_helmet - qizil
}
CLASS_NAMES = {
    0: "HELMET",
    1: "NO_HELMET",
}


def draw_yolo_bboxes(img_path, lbl_path, output_path):
    img = cv2.imread(str(img_path))
    if img is None:
        return False
    h, w = img.shape[:2]

    if not Path(lbl_path).exists():
        cv2.imwrite(str(output_path), img)
        return True

    for line in Path(lbl_path).read_text().strip().split("\n"):
        parts = line.strip().split()
        if len(parts) < 5:
            continue
        cls_id = int(parts[0])
        xc, yc, bw, bh = map(float, parts[1:5])
        # YOLO -> pixel coords
        x1 = int((xc - bw / 2) * w)
        y1 = int((yc - bh / 2) * h)
        x2 = int((xc + bw / 2) * w)
        y2 = int((yc + bh / 2) * h)
        color = CLASS_COLORS.get(cls_id, (255, 255, 0))
        label = CLASS_NAMES.get(cls_id, f"cls{cls_id}")
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        cv2.putText(img, label, (x1, max(20, y1 - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    cv2.imwrite(str(output_path), img)
    return True


def main():
    if len(sys.argv) < 2:
        print("Ishlatish: python visualize.py <dataset> [split] [count]")
        sys.exit(1)
    dataset = Path(sys.argv[1])
    split = sys.argv[2] if len(sys.argv) > 2 else "train"
    count = int(sys.argv[3]) if len(sys.argv) > 3 else 10

    img_dir = dataset / "images" / split
    lbl_dir = dataset / "labels" / split
    out_dir = dataset / "visualized" / split
    out_dir.mkdir(parents=True, exist_ok=True)

    images = list(img_dir.glob("*"))
    images = [i for i in images if i.suffix.lower() in (".jpg", ".jpeg", ".png")]
    random.shuffle(images)
    images = images[:count]

    print(f"[+] {len(images)} ta tasodifiy rasm tahlil qilinmoqda...")
    for img_path in images:
        lbl_path = lbl_dir / (img_path.stem + ".txt")
        out_path = out_dir / img_path.name
        if draw_yolo_bboxes(img_path, lbl_path, out_path):
            print(f"  [+] {out_path}")
    print(f"\n[OK] Natija: {out_dir} (rasmlarni ko'rish mumkin)")


if __name__ == "__main__":
    main()
