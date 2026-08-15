"""
PASCAL VOC (XML) -> YOLO (TXT) konvertor

SHWD, Kaggle Hard Hat va boshqa VOC formatdagi datasetlar uchun.

ISHLATISH:
    python convert_voc_to_yolo.py --voc-dir <VOC papka> --output <YOLO papka>

Misol:
    python convert_voc_to_yolo.py \
        --voc-dir "D:\\sergak dasturi\\kaska\\datasets\\shwd" \
        --output "D:\\sergak dasturi\\kaska\\datasets\\shwd_yolo"
"""
import argparse
import os
import xml.etree.ElementTree as ET
from pathlib import Path
import shutil

# Klass xaritalash - barcha datasetlarda turli nomlar bor, biz 2 tagacha tushiramiz
CLASS_MAP = {
    # Helmet variantlar (kaska bor)
    "helmet": 0,
    "hat": 0,
    "hard hat": 0,
    "hardhat": 0,
    "with helmet": 0,
    "with_helmet": 0,
    "wearing_helmet": 0,

    # No helmet (kaska yo'q - bizning maqsadimiz!)
    "no_helmet": 1,
    "no-helmet": 1,
    "no helmet": 1,
    "without_helmet": 1,
    "without helmet": 1,
    "head": 1,         # ko'pchilik datasetda "head" = kaskasiz bosh
    "person": 1,       # ehtiyot bo'lib - faqat agar dataset shunday belgilangan bo'lsa
}

YOLO_CLASSES = ["helmet", "no_helmet"]


def voc_to_yolo_bbox(size, box):
    """VOC bbox (xmin, ymin, xmax, ymax) -> YOLO (x_center, y_center, w, h) [normalized]"""
    dw = 1.0 / size[0]
    dh = 1.0 / size[1]
    x = (box[0] + box[2]) / 2.0 - 1
    y = (box[1] + box[3]) / 2.0 - 1
    w = box[2] - box[0]
    h = box[3] - box[1]
    return x * dw, y * dh, w * dw, h * dh


def convert_xml(xml_path, output_txt, image_extensions=(".jpg", ".jpeg", ".png")):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    size = root.find("size")
    if size is None:
        return False, "no <size>"
    w = int(size.find("width").text)
    h = int(size.find("height").text)

    lines = []
    for obj in root.findall("object"):
        cls_name = obj.find("name").text.lower().strip()
        if cls_name not in CLASS_MAP:
            print(f"  [!] noma'lum klass: '{cls_name}' (o'tkazib yuborildi)")
            continue
        cls_id = CLASS_MAP[cls_name]
        xmlbox = obj.find("bndbox")
        b = (
            float(xmlbox.find("xmin").text),
            float(xmlbox.find("ymin").text),
            float(xmlbox.find("xmax").text),
            float(xmlbox.find("ymax").text),
        )
        bb = voc_to_yolo_bbox((w, h), b)
        lines.append(f"{cls_id} {bb[0]:.6f} {bb[1]:.6f} {bb[2]:.6f} {bb[3]:.6f}")

    with open(output_txt, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return True, len(lines)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--voc-dir", required=True, help="VOC dataset papkasi (Annotations va JPEGImages bilan)")
    p.add_argument("--output", required=True, help="Natija YOLO papkasi")
    args = p.parse_args()

    voc_root = Path(args.voc_dir)
    out_root = Path(args.output)

    # VOC papka strukturasi: Annotations/ va JPEGImages/ (yoki images/)
    ann_dir = None
    img_dir = None
    for candidate in ["Annotations", "annotations"]:
        if (voc_root / candidate).exists():
            ann_dir = voc_root / candidate
            break
    for candidate in ["JPEGImages", "images", "JPEG"]:
        if (voc_root / candidate).exists():
            img_dir = voc_root / candidate
            break

    if not ann_dir:
        print(f"[X] Annotations papkasi topilmadi: {voc_root}")
        return
    if not img_dir:
        print(f"[X] Images papkasi topilmadi: {voc_root}")
        return

    print(f"[+] VOC manba:   {voc_root}")
    print(f"    Annotations: {ann_dir}")
    print(f"    Images:      {img_dir}")

    out_img = out_root / "images"
    out_lbl = out_root / "labels"
    out_img.mkdir(parents=True, exist_ok=True)
    out_lbl.mkdir(parents=True, exist_ok=True)

    total = 0
    ok = 0
    total_boxes = 0
    for xml_file in ann_dir.glob("*.xml"):
        total += 1
        stem = xml_file.stem
        # Mos rasm topish
        src_img = None
        for ext in [".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"]:
            cand = img_dir / (stem + ext)
            if cand.exists():
                src_img = cand
                break
        if not src_img:
            continue

        # Label fayl
        txt_path = out_lbl / (stem + ".txt")
        success, n = convert_xml(xml_file, txt_path)
        if not success:
            continue
        # Rasmni ko'chirish
        dst_img = out_img / src_img.name
        if not dst_img.exists():
            shutil.copy2(src_img, dst_img)
        ok += 1
        total_boxes += n if isinstance(n, int) else 0
        if ok % 500 == 0:
            print(f"  {ok}/{total} ta fayl konvertatsiyalandi...")

    print(f"\n[OK] Yakuniy: {ok}/{total} ta XML konvertatsiyalandi")
    print(f"     Jami bounding box: {total_boxes}")
    print(f"     Natija: {out_root}")


if __name__ == "__main__":
    main()
