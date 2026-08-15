"""
3 ta yangi datasetni standartlashtirish (VOC -> YOLO konversiya):
  1. SHEL5K          (9rcv8mm682-4)             -> shel5k_yolo/
  2. GDUT-HWD        (Annotations + JPEGImages) -> gdut_hwd_yolo/
  3. SHWD (VOC2028)  (VOC2028)                  -> shwd_yolo/

Hammasi YOLO formatga (helmet=0, no_helmet=1) konvertatsiya qilinadi.
"""
import random
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

DATASETS_ROOT = Path(r"D:\sergak dasturi\kaska\datasets")
random.seed(42)


def voc_box_to_yolo(size, box):
    """VOC bbox (xmin,ymin,xmax,ymax) -> YOLO (cx,cy,w,h) normallashtirilgan."""
    w_img, h_img = size
    cx = (box[0] + box[2]) / 2.0 / w_img
    cy = (box[1] + box[3]) / 2.0 / h_img
    w = (box[2] - box[0]) / w_img
    h = (box[3] - box[1]) / h_img
    return cx, cy, w, h


def write_yaml(path, train_rel="images/train", val_rel="images/valid", test_rel=None):
    lines = [f"path: {path.parent.as_posix()}", f"train: {train_rel}", f"val: {val_rel}"]
    if test_rel:
        lines.append(f"test: {test_rel}")
    lines.append("")
    lines.append("nc: 2")
    lines.append("names:")
    lines.append("  0: helmet")
    lines.append("  1: no_helmet")
    path.write_text("\n".join(lines), encoding="utf-8")


def convert_xml(xml_path, out_txt, class_map):
    """VOC XML ni YOLO TXT ga konvertatsiya qiladi. class_map: {'name': 0/1/None}"""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        size_elem = root.find("size")
        if size_elem is None:
            return False
        w = int(size_elem.find("width").text)
        h = int(size_elem.find("height").text)
        if w <= 0 or h <= 0:
            return False
        lines = []
        for obj in root.findall("object"):
            name_elem = obj.find("name")
            if name_elem is None:
                continue
            name = name_elem.text.strip().lower()
            new_cls = class_map.get(name)
            if new_cls is None:
                continue
            bb = obj.find("bndbox")
            try:
                xmin = float(bb.find("xmin").text)
                ymin = float(bb.find("ymin").text)
                xmax = float(bb.find("xmax").text)
                ymax = float(bb.find("ymax").text)
            except (AttributeError, ValueError):
                continue
            # Cheklash (rasm chegarasidan oshmasin)
            xmin = max(0, min(xmin, w))
            ymin = max(0, min(ymin, h))
            xmax = max(0, min(xmax, w))
            ymax = max(0, min(ymax, h))
            if xmax <= xmin or ymax <= ymin:
                continue
            cx, cy, bw, bh = voc_box_to_yolo((w, h), (xmin, ymin, xmax, ymax))
            lines.append(f"{new_cls} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")
        if not lines:
            return False
        out_txt.write_text("\n".join(lines))
        return True
    except Exception as e:
        return False


def find_image(stem, img_dir, exts=(".jpg", ".jpeg", ".png", ".bmp")):
    """Stem bo'yicha rasm faylini topish."""
    for ext in exts:
        cand = img_dir / (stem + ext)
        if cand.exists():
            return cand
    return None


# ============================================================
# 1) SHEL5K
# ============================================================
SHEL5K_CLASS_MAP = {
    "helmet": 0,
    "head": 1,
    # Quyidagilar dublikat yoki kontekst — skip:
    "head_with_helmet": None,
    "person_with_helmet": None,
    "person_no_helmet": None,
    "face": None,
    "person": None,
}


def step1_shel5k():
    print("\n[1/3] SHEL5K (9rcv8mm682-4)")
    print("-" * 60)
    src = DATASETS_ROOT / "9rcv8mm682-4" / "Safety Helmet Wearing Dataset"
    if not src.exists():
        print(f"  [!] yo'q: {src}")
        return
    src_img = src / "Images"
    src_ann = src / "Annotations"
    if not src_img.exists() or not src_ann.exists():
        print(f"  [X] Images/ yoki Annotations/ topilmadi")
        return

    out = DATASETS_ROOT / "shel5k_yolo"
    out_img_train = out / "images" / "train"
    out_lbl_train = out / "labels" / "train"
    out_img_val = out / "images" / "valid"
    out_lbl_val = out / "labels" / "valid"
    for d in [out_img_train, out_lbl_train, out_img_val, out_lbl_val]:
        d.mkdir(parents=True, exist_ok=True)

    xmls = sorted(src_ann.glob("*.xml"))
    print(f"  [+] {len(xmls)} ta XML topildi, konvertatsiya boshlanmoqda...")
    ok = 0
    skipped = 0
    for i, xml in enumerate(xmls):
        stem = xml.stem
        img = find_image(stem, src_img)
        if not img:
            skipped += 1
            continue
        # 90/10 train/valid split
        is_train = random.random() < 0.9
        out_lbl = (out_lbl_train if is_train else out_lbl_val) / (stem + ".txt")
        out_img = (out_img_train if is_train else out_img_val) / img.name
        if convert_xml(xml, out_lbl, SHEL5K_CLASS_MAP):
            shutil.copy2(img, out_img)
            ok += 1
            if (i + 1) % 1000 == 0:
                print(f"    {i+1}/{len(xmls)}")
        else:
            skipped += 1
    print(f"  [+] {ok} ta yozildi, {skipped} ta skip")
    write_yaml(out / "data.yaml")
    print(f"  [+] data.yaml: {out / 'data.yaml'}")


# ============================================================
# 2) GDUT-HWD (root: Annotations + JPEGImages)
# ============================================================
GDUT_HWD_CLASS_MAP = {
    "white": 0,
    "yellow": 0,
    "red": 0,
    "blue": 0,
    "none": 1,
}


def step2_gdut_hwd():
    print("\n[2/3] GDUT-HWD (root: Annotations + JPEGImages)")
    print("-" * 60)
    src_ann = DATASETS_ROOT / "Annotations"
    src_img = DATASETS_ROOT / "JPEGImages"
    if not src_ann.exists() or not src_img.exists():
        print(f"  [X] Annotations/ yoki JPEGImages/ topilmadi (datasets/ root)")
        return

    out = DATASETS_ROOT / "gdut_hwd_yolo"
    out_img_train = out / "images" / "train"
    out_lbl_train = out / "labels" / "train"
    out_img_val = out / "images" / "valid"
    out_lbl_val = out / "labels" / "valid"
    for d in [out_img_train, out_lbl_train, out_img_val, out_lbl_val]:
        d.mkdir(parents=True, exist_ok=True)

    xmls = sorted(src_ann.glob("*.xml"))
    print(f"  [+] {len(xmls)} ta XML topildi, konvertatsiya boshlanmoqda...")
    ok = 0
    skipped = 0
    for i, xml in enumerate(xmls):
        stem = xml.stem
        img = find_image(stem, src_img)
        if not img:
            skipped += 1
            continue
        is_train = random.random() < 0.9
        out_lbl = (out_lbl_train if is_train else out_lbl_val) / (stem + ".txt")
        out_img = (out_img_train if is_train else out_img_val) / img.name
        if convert_xml(xml, out_lbl, GDUT_HWD_CLASS_MAP):
            shutil.copy2(img, out_img)
            ok += 1
            if (i + 1) % 500 == 0:
                print(f"    {i+1}/{len(xmls)}")
        else:
            skipped += 1
    print(f"  [+] {ok} ta yozildi, {skipped} ta skip")
    write_yaml(out / "data.yaml")
    print(f"  [+] data.yaml: {out / 'data.yaml'}")


# ============================================================
# 3) SHWD (VOC2028)
# ============================================================
SHWD_CLASS_MAP = {
    "hat": 0,        # helmet
    "person": 1,     # no_helmet (head bez kaska)
    "dog": None,     # shum (xato) - skip
}


def step3_shwd():
    print("\n[3/3] SHWD (VOC2028)")
    print("-" * 60)
    src = DATASETS_ROOT / "VOC2028"
    if not src.exists():
        print(f"  [!] yo'q: {src}")
        return
    src_img = src / "JPEGImages"
    src_ann = src / "Annotations"
    sets_dir = src / "ImageSets" / "Main"
    if not src_img.exists() or not src_ann.exists():
        print(f"  [X] JPEGImages/ yoki Annotations/ topilmadi")
        return

    out = DATASETS_ROOT / "shwd_yolo"
    splits_map = {}
    if sets_dir.exists() and (sets_dir / "train.txt").exists():
        # Asl split fayllarini ishlatamiz
        for split_name, file_name in [("train", "train.txt"), ("valid", "val.txt"), ("test", "test.txt")]:
            f = sets_dir / file_name
            if f.exists():
                stems = [s.strip() for s in f.read_text().split("\n") if s.strip()]
                splits_map[split_name] = stems
        print(f"  [+] ImageSets ishlatilmoqda: train={len(splits_map.get('train',[]))}, "
              f"val={len(splits_map.get('valid',[]))}, test={len(splits_map.get('test',[]))}")
    else:
        # Random 80/10/10 split
        all_stems = sorted([f.stem for f in src_ann.glob("*.xml")])
        random.shuffle(all_stems)
        n = len(all_stems)
        n_train = int(n * 0.8)
        n_val = int(n * 0.1)
        splits_map = {
            "train": all_stems[:n_train],
            "valid": all_stems[n_train:n_train + n_val],
            "test": all_stems[n_train + n_val:],
        }
        print(f"  [+] Random split: train={len(splits_map['train'])}, "
              f"val={len(splits_map['valid'])}, test={len(splits_map['test'])}")

    for split_name in ["train", "valid", "test"]:
        (out / "images" / split_name).mkdir(parents=True, exist_ok=True)
        (out / "labels" / split_name).mkdir(parents=True, exist_ok=True)

    total_ok = 0
    total_skipped = 0
    for split_name, stems in splits_map.items():
        out_img = out / "images" / split_name
        out_lbl = out / "labels" / split_name
        ok = 0
        skipped = 0
        for i, stem in enumerate(stems):
            xml = src_ann / (stem + ".xml")
            img = find_image(stem, src_img)
            if not xml.exists() or not img:
                skipped += 1
                continue
            dst_lbl = out_lbl / (stem + ".txt")
            dst_img = out_img / img.name
            if convert_xml(xml, dst_lbl, SHWD_CLASS_MAP):
                shutil.copy2(img, dst_img)
                ok += 1
                if (i + 1) % 1000 == 0:
                    print(f"    [{split_name}] {i+1}/{len(stems)}")
            else:
                skipped += 1
        total_ok += ok
        total_skipped += skipped
        print(f"  [+] [{split_name}] {ok} yozildi, {skipped} skip")
    print(f"  [JAMI] {total_ok} ta yozildi, {total_skipped} ta skip")
    write_yaml(out / "data.yaml", test_rel="images/test")
    print(f"  [+] data.yaml: {out / 'data.yaml'}")


def main():
    print("=" * 70)
    print("  3 ta yangi datasetni YOLO formatiga konvertatsiya")
    print("  Hammasi -> 2 klass (helmet=0, no_helmet=1)")
    print("=" * 70)
    step1_shel5k()
    step2_gdut_hwd()
    step3_shwd()
    print()
    print("=" * 70)
    print("  TUGADI")
    print("=" * 70)
    print()
    print("  Endi merge ishga tushirish:")
    print(r'    python scripts\final_merge.py')


if __name__ == "__main__":
    main()
