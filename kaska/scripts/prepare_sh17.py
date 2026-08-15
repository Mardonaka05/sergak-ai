"""
SH17 datasetini YOLO formatga konvertatsiya (IoU filter bilan).

SH17 — 17 ta klassli PPE dataset. Bizga faqat ikkitasi kerak:
  - helmet (927 ta)  -> 0
  - head (11,985 ta) -> 1 (lekin faqat ustida helmet bo'lmaganlari)

MUHIM: SH17 da `head` va `helmet` BIR VAQTNING o'zida bbox sifatida
qo'yilgan — yani kaska kiygan odam uchun ham helmet, ham head bbox bor.
Shuning uchun IoU filter qo'llaymiz:
  - Agar head bbox helmet bbox bilan IoU > 0.3 bo'lsa — bu kaska kiygan
    odamning boshi, no_helmet emas — SKIP qilamiz.
  - Aks holda head bbox haqiqatan ham kaskasiz — saqlaymiz.

Manba:  datasets/voc_labels/ + datasets/images/
Natija: datasets/sh17_yolo/images/{train,valid}/ + labels/{train,valid}/
"""
import random
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("[!] Pillow topilmadi, pip install pillow ishlatilsin")

DATASETS_ROOT = Path(r"D:\sergak dasturi\kaska\datasets")
SRC_IMG = DATASETS_ROOT / "images"
SRC_ANN = DATASETS_ROOT / "voc_labels"
OUT = DATASETS_ROOT / "sh17_yolo"

IOU_THRESHOLD = 0.30  # head va helmet kesishishi chegarasi
MAX_SIDE = 1280       # rasmlarni bu o'lchamgacha kichraytirish (disk tejash)
JPEG_QUALITY = 88     # JPEG saqlash sifati

random.seed(42)


def save_resized(src_path, dst_path, max_side=MAX_SIDE):
    """Rasmni max_side dan oshmaydigan o'lchamga resize qilib saqlash."""
    if not HAS_PIL:
        shutil.copy2(src_path, dst_path)
        return
    try:
        img = Image.open(src_path)
        # RGB ga konvertatsiya (P/PA/RGBA bo'lsa)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        w, h = img.size
        if max(w, h) > max_side:
            if w >= h:
                new_w = max_side
                new_h = int(h * max_side / w)
            else:
                new_h = max_side
                new_w = int(w * max_side / h)
            img = img.resize((new_w, new_h), Image.LANCZOS)
        # Har doim JPEG sifatida saqlaymiz (joy tejaymiz)
        dst_path = dst_path.with_suffix(".jpg")
        img.save(dst_path, "JPEG", quality=JPEG_QUALITY, optimize=True)
    except Exception:
        # Xatolik bo'lsa oddiy copy
        shutil.copy2(src_path, dst_path)


def iou(box1, box2):
    """IoU = Intersection over Union, [x1, y1, x2, y2] formatda."""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    if x2 <= x1 or y2 <= y1:
        return 0.0
    inter = (x2 - x1) * (y2 - y1)
    a1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    a2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = a1 + a2 - inter
    return inter / union if union > 0 else 0.0


def voc_to_yolo(size, box):
    """[x1,y1,x2,y2] -> [cx,cy,w,h] normalized."""
    w_img, h_img = size
    cx = (box[0] + box[2]) / 2.0 / w_img
    cy = (box[1] + box[3]) / 2.0 / h_img
    w = (box[2] - box[0]) / w_img
    h = (box[3] - box[1]) / h_img
    return cx, cy, w, h


def parse_xml(xml_path):
    """XML dan rasm o'lcham va helmet/head bbox larini qaytarish."""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        size = root.find("size")
        w = int(size.find("width").text)
        h = int(size.find("height").text)
        helmets = []
        heads = []
        for obj in root.findall("object"):
            name = obj.find("name").text.strip().lower()
            if name not in ("helmet", "head"):
                continue
            bb = obj.find("bndbox")
            try:
                xmin = float(bb.find("xmin").text)
                ymin = float(bb.find("ymin").text)
                xmax = float(bb.find("xmax").text)
                ymax = float(bb.find("ymax").text)
            except Exception:
                continue
            # Cheklash
            xmin = max(0, min(xmin, w))
            ymin = max(0, min(ymin, h))
            xmax = max(0, min(xmax, w))
            ymax = max(0, min(ymax, h))
            if xmax <= xmin or ymax <= ymin:
                continue
            box = [xmin, ymin, xmax, ymax]
            if name == "helmet":
                helmets.append(box)
            else:
                heads.append(box)
        return w, h, helmets, heads
    except Exception:
        return None, None, None, None


def find_image(stem):
    """SH17 da .jpg yoki .jpeg bo'lishi mumkin."""
    for ext in (".jpg", ".jpeg", ".png"):
        cand = SRC_IMG / (stem + ext)
        if cand.exists():
            return cand
    return None


def write_yaml(path):
    content = f"""path: {path.parent.as_posix()}
train: images/train
val: images/valid

nc: 2
names:
  0: helmet
  1: no_helmet
"""
    path.write_text(content, encoding="utf-8")


def main():
    print("=" * 70)
    print("  SH17 -> YOLO konversiya (IoU filter bilan)")
    print(f"  IoU chegara: {IOU_THRESHOLD}")
    print("=" * 70)

    if not SRC_ANN.exists() or not SRC_IMG.exists():
        print(f"  [X] Topilmadi: {SRC_ANN} yoki {SRC_IMG}")
        return

    # Output papkalarni tozalash va yangidan yaratish
    if OUT.exists():
        print(f"  [!] Eski {OUT.name}/ tozalanmoqda...")
        shutil.rmtree(OUT)
    out_img_t = OUT / "images" / "train"
    out_lbl_t = OUT / "labels" / "train"
    out_img_v = OUT / "images" / "valid"
    out_lbl_v = OUT / "labels" / "valid"
    for d in [out_img_t, out_lbl_t, out_img_v, out_lbl_v]:
        d.mkdir(parents=True, exist_ok=True)

    xmls = sorted(SRC_ANN.glob("*.xml"))
    print(f"\n  [+] {len(xmls)} ta XML topildi")

    # Statistika
    total_helmet = 0       # final helmet bbox
    total_no_helmet = 0    # final no_helmet bbox (filterdan o'tgan head)
    skipped_heads = 0      # IoU > threshold sababli skip qilingan head
    img_written = 0
    img_no_data = 0        # umuman helmet/head topilmagan rasmlar
    img_no_img_file = 0    # rasm fayli topilmagan

    print("\n  Konversiya boshlanmoqda...")
    for i, xml in enumerate(xmls):
        w, h, helmets, heads = parse_xml(xml)
        if w is None:
            continue

        img_path = find_image(xml.stem)
        if not img_path:
            img_no_img_file += 1
            continue

        # IoU filter: head ustida helmet bormi?
        valid_heads = []
        for head_box in heads:
            is_helmet_wearer = False
            for helmet_box in helmets:
                if iou(head_box, helmet_box) > IOU_THRESHOLD:
                    is_helmet_wearer = True
                    break
            if not is_helmet_wearer:
                valid_heads.append(head_box)
            else:
                skipped_heads += 1

        # YOLO satrlari
        lines = []
        for box in helmets:
            cx, cy, bw, bh = voc_to_yolo((w, h), box)
            lines.append(f"0 {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")
            total_helmet += 1
        for box in valid_heads:
            cx, cy, bw, bh = voc_to_yolo((w, h), box)
            lines.append(f"1 {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")
            total_no_helmet += 1

        if not lines:
            img_no_data += 1
            continue

        # 90/10 train/valid split
        is_train = random.random() < 0.9
        out_img = (out_img_t if is_train else out_img_v) / img_path.name
        out_lbl = (out_lbl_t if is_train else out_lbl_v) / (xml.stem + ".txt")
        out_lbl.write_text("\n".join(lines))
        # Rasmni resize qilib JPEG sifatida saqlash (disk tejash)
        save_resized(img_path, out_img)
        img_written += 1

        if (i + 1) % 1000 == 0:
            print(f"    {i+1}/{len(xmls)} ishlandi (yozildi: {img_written})")

    write_yaml(OUT / "data.yaml")

    print()
    print("=" * 70)
    print("  YAKUNIY NATIJA")
    print("=" * 70)
    print(f"  Yozilgan rasmlar:        {img_written:,}")
    print(f"  helmet bbox:             {total_helmet:,}")
    print(f"  no_helmet bbox:          {total_no_helmet:,}")
    print(f"  IoU filter bilan skip:   {skipped_heads:,} (head ustida helmet bor)")
    print(f"  Helmet/head topilmagan:  {img_no_data:,} ta rasm")
    print(f"  Rasm fayli topilmagan:   {img_no_img_file:,}")
    print(f"  Joylashish:              {OUT}")
    print(f"  data.yaml:               {OUT / 'data.yaml'}")


if __name__ == "__main__":
    main()
