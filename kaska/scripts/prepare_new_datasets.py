"""
Yangi yuklab olingan datasetlarni standartlashtirish.

1. kaggle_yolo_helmethead → data.yaml ni helm/helm/ ga yaratish
2. kaggle_construction_safety → data.yaml ni css-data/ ga yaratish (10 klassdan 2 tasi qiziqarli)
3. kaggle_hardhat_andrewmvd → VOC XML dan YOLO ga konvertatsiya
"""
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

DATASETS_ROOT = Path(r"D:\sergak dasturi\kaska\datasets")


def write_yaml(path, classes, train_rel="images/train", val_rel="images/valid", test_rel=""):
    lines = [f"path: {path.parent.as_posix()}", f"train: {train_rel}", f"val: {val_rel}"]
    if test_rel:
        lines.append(f"test: {test_rel}")
    lines.append("")
    lines.append(f"nc: {len(classes)}")
    lines.append("names:")
    for i, n in enumerate(classes):
        lines.append(f"  {i}: {n}")
    path.write_text("\n".join(lines), encoding="utf-8")


def step1_helmethead():
    """kaggle_yolo_helmethead uchun data.yaml yaratish."""
    print("\n[1/3] kaggle_yolo_helmethead")
    root = DATASETS_ROOT / "kaggle_yolo_helmethead" / "helm" / "helm"
    if not root.exists():
        print(f"  [!] yo'q: {root}")
        return
    yaml_path = root / "data.yaml"
    write_yaml(
        yaml_path,
        classes=["head", "helmet"],
        train_rel="images/train",
        val_rel="images/valid",
        test_rel="images/test",
    )
    print(f"  [+] yaratildi: {yaml_path}")
    # Sanash
    n = sum(1 for f in (root / "images").rglob("*") if f.suffix.lower() in (".jpg", ".jpeg", ".png"))
    print(f"  [+] {n} ta rasm")


def step2_construction():
    """kaggle_construction_safety uchun data.yaml yaratish."""
    print("\n[2/3] kaggle_construction_safety")
    root = DATASETS_ROOT / "kaggle_construction_safety" / "css-data"
    if not root.exists():
        print(f"  [!] yo'q: {root}")
        return
    yaml_path = root / "data.yaml"
    # Klasslarning to'liq ro'yxati - 10 klass
    classes = ["Hardhat", "Mask", "NO-Hardhat", "NO-Mask", "NO-Safety Vest",
               "Person", "Safety Cone", "Safety Vest", "machinery", "vehicle"]
    write_yaml(yaml_path, classes,
               train_rel="train/images", val_rel="valid/images", test_rel="test/images")
    print(f"  [+] yaratildi: {yaml_path}")
    # Sanash
    n = sum(1 for f in root.rglob("*") if f.suffix.lower() in (".jpg", ".jpeg", ".png"))
    print(f"  [+] {n} ta rasm (faqat Hardhat=0 va NO-Hardhat=2 bizga kerak)")


def voc_box_to_yolo(size, box):
    dw = 1.0 / size[0]
    dh = 1.0 / size[1]
    x = (box[0] + box[2]) / 2.0
    y = (box[1] + box[3]) / 2.0
    w = box[2] - box[0]
    h = box[3] - box[1]
    return x * dw, y * dh, w * dw, h * dh


CLASS_MAP_ANDREWMVD = {"helmet": 0, "head": 1, "person": 1}


def convert_voc_xml(xml_path, output_txt):
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        size_elem = root.find("size")
        w = int(size_elem.find("width").text)
        h = int(size_elem.find("height").text)
        lines = []
        for obj in root.findall("object"):
            name = obj.find("name").text.lower().strip()
            if name not in CLASS_MAP_ANDREWMVD:
                continue
            cls = CLASS_MAP_ANDREWMVD[name]
            bb = obj.find("bndbox")
            box = (float(bb.find("xmin").text), float(bb.find("ymin").text),
                   float(bb.find("xmax").text), float(bb.find("ymax").text))
            x, y, bw, bh = voc_box_to_yolo((w, h), box)
            lines.append(f"{cls} {x:.6f} {y:.6f} {bw:.6f} {bh:.6f}")
        if lines:
            output_txt.write_text("\n".join(lines))
            return True
    except Exception:
        pass
    return False


def step3_andrewmvd():
    """kaggle_hardhat_andrewmvd ni VOC dan YOLO ga konvertatsiya."""
    print("\n[3/3] kaggle_hardhat_andrewmvd (VOC -> YOLO)")
    src = DATASETS_ROOT / "kaggle_hardhat_andrewmvd"
    if not src.exists():
        print(f"  [!] yo'q: {src}")
        return

    src_img = src / "images"
    src_ann = src / "annotations"
    if not src_img.exists() or not src_ann.exists():
        print(f"  [X] images/ yoki annotations/ topilmadi")
        return

    # Yangi YOLO format papkasi yaratamiz
    out = DATASETS_ROOT / "kaggle_hardhat_andrewmvd_yolo"
    # Train uchun 90% yozamiz, valid uchun 10%
    import random
    random.seed(42)

    out_img_train = out / "images" / "train"
    out_lbl_train = out / "labels" / "train"
    out_img_val = out / "images" / "valid"
    out_lbl_val = out / "labels" / "valid"
    for d in [out_img_train, out_lbl_train, out_img_val, out_lbl_val]:
        d.mkdir(parents=True, exist_ok=True)

    xmls = sorted(src_ann.glob("*.xml"))
    print(f"  [+] {len(xmls)} ta XML topildi, konvertatsiya boshlanmoqda...")

    ok = 0
    for i, xml in enumerate(xmls):
        stem = xml.stem
        img = None
        for ext in [".png", ".jpg", ".jpeg"]:
            cand = src_img / (stem + ext)
            if cand.exists():
                img = cand
                break
        if not img:
            continue
        # Train/valid split
        is_train = random.random() < 0.9
        out_lbl = (out_lbl_train if is_train else out_lbl_val) / (stem + ".txt")
        out_img = (out_img_train if is_train else out_img_val) / img.name
        if convert_voc_xml(xml, out_lbl):
            shutil.copy2(img, out_img)
            ok += 1
            if (i + 1) % 1000 == 0:
                print(f"    {i+1}/{len(xmls)}")
    print(f"  [+] {ok} ta juftlik yozildi: {out}")

    # data.yaml
    write_yaml(
        out / "data.yaml",
        classes=["helmet", "no_helmet"],
        train_rel="images/train", val_rel="images/valid",
    )
    print(f"  [+] data.yaml yaratildi")


def main():
    print("=" * 70)
    print("  Yangi datasetlarni standartlashtirish (data.yaml yaratish + konversiya)")
    print("=" * 70)
    step1_helmethead()
    step2_construction()
    step3_andrewmvd()
    print()
    print("=" * 70)
    print("  TUGADI")
    print("=" * 70)
    print()
    print("  Endi merge ishga tushirish:")
    print(r'    .\2_merge_datasets.bat')


if __name__ == "__main__":
    main()
