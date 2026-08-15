"""
SERGAK AI - SIGARET DATASETLAR YAKUNIY MERGE (v2 - 1 KLASS)
=============================================================
6 ta prepared datasetni 80/15/5 (train/val/test) ga bo'lib birlashtirish.

Input:  D:\\sergak dasturi\\sergak_smoking\\prepared\\
Output: D:\\sergak dasturi\\sergak_smoking\\merged\\
         ├── images/train, val, test
         ├── labels/train, val, test
         └── data.yaml (1 klass: smoking)
"""
import random
import shutil
from pathlib import Path

PREPARED_DIR = Path(r"D:\sergak dasturi\sergak_smoking\prepared")
MERGED_DIR = Path(r"D:\sergak dasturi\sergak_smoking\merged")

SPLIT_RATIO = {"train": 0.80, "val": 0.15, "test": 0.05}
SEED = 42
random.seed(SEED)


def log(msg, lvl="INFO"):
    symbols = {"INFO": "[i]", "OK": "[+]", "WARN": "[!]", "ERR": "[X]",
               "SKIP": "[-]", "PROC": "[->"}
    print(f"  {symbols.get(lvl, '[?]')} {msg}")


def header(title):
    print()
    print("=" * 72)
    print(f"  {title}")
    print("=" * 72)


def main():
    print()
    print("=" * 72)
    print("  SERGAK AI - SIGARET DATASETLAR YAKUNIY MERGE (v2)")
    print("=" * 72)
    print(f"  Input:   {PREPARED_DIR}")
    print(f"  Output:  {MERGED_DIR}")
    print(f"  Split:   train={SPLIT_RATIO['train']*100:.0f}%  val={SPLIT_RATIO['val']*100:.0f}%  test={SPLIT_RATIO['test']*100:.0f}%")
    print()

    if not PREPARED_DIR.exists():
        print(f"[X] Topilmadi: {PREPARED_DIR}")
        return

    # Eski merged'ni tozalash
    if MERGED_DIR.exists():
        log("Eski merged tozalanmoqda...", "WARN")
        shutil.rmtree(MERGED_DIR)

    # Folder strukturasi
    for split in ["train", "val", "test"]:
        (MERGED_DIR / "images" / split).mkdir(parents=True, exist_ok=True)
        (MERGED_DIR / "labels" / split).mkdir(parents=True, exist_ok=True)

    # ============================================================
    # 1) Barcha juftliklarni yig'ish
    # ============================================================
    header("1) Barcha juftliklarni yig'ish")
    all_pairs = []
    ds_counts = {}

    for ds_dir in sorted(PREPARED_DIR.iterdir()):
        if not ds_dir.is_dir():
            continue
        imgs_dir = ds_dir / "images"
        labels_dir = ds_dir / "labels"
        if not imgs_dir.exists() or not labels_dir.exists():
            log(f"SKIP: {ds_dir.name} (papka yo'q)", "SKIP")
            continue

        n_before = len(all_pairs)
        for img in imgs_dir.iterdir():
            if img.suffix.lower() not in (".jpg", ".jpeg", ".png", ".bmp"):
                continue
            lbl = labels_dir / (img.stem + ".txt")
            if not lbl.exists():
                continue
            all_pairs.append({
                "img": img,
                "lbl": lbl,
                "ds_name": ds_dir.name,
            })
        added = len(all_pairs) - n_before
        ds_counts[ds_dir.name] = added
        log(f"{ds_dir.name:<40s} {added:>7,} ta", "OK")

    total = len(all_pairs)
    print()
    print(f"  📊 JAMI: {total:,} ta rasm-label juftligi")
    print()

    if total == 0:
        log("Juftlik topilmadi - to'xtatildi", "ERR")
        return

    # ============================================================
    # 2) Aralashtirish va bo'lish
    # ============================================================
    header("2) Train/Val/Test split")

    random.shuffle(all_pairs)

    n_train = int(total * SPLIT_RATIO["train"])
    n_val = int(total * SPLIT_RATIO["val"])
    n_test = total - n_train - n_val

    splits = {
        "train": all_pairs[:n_train],
        "val": all_pairs[n_train:n_train + n_val],
        "test": all_pairs[n_train + n_val:],
    }

    log(f"train: {len(splits['train']):,}", "OK")
    log(f"val:   {len(splits['val']):,}", "OK")
    log(f"test:  {len(splits['test']):,}", "OK")

    # ============================================================
    # 3) Fayllarni ko'chirish
    # ============================================================
    header("3) Fayllarni ko'chirish")

    total_bbox = 0
    for split_name, items in splits.items():
        img_out = MERGED_DIR / "images" / split_name
        lbl_out = MERGED_DIR / "labels" / split_name

        log(f"[{split_name}] {len(items):,} ta...", "PROC")
        copied = 0
        for i, p in enumerate(items):
            # Yangi nom (noyob bo'lishi uchun ds_name prefiks)
            new_stem = f"{p['ds_name']}__{p['img'].stem}"
            dst_img = img_out / f"{new_stem}{p['img'].suffix}"
            dst_lbl = lbl_out / f"{new_stem}.txt"

            try:
                shutil.copy2(str(p['img']), str(dst_img))
                shutil.copy2(str(p['lbl']), str(dst_lbl))

                # Bbox sanash
                content = dst_lbl.read_text().strip()
                if content:
                    for line in content.split("\n"):
                        if line.split():
                            total_bbox += 1

                copied += 1
                if (i + 1) % 5000 == 0:
                    print(f"    {i+1:,}/{len(items):,}")
            except Exception as e:
                log(f"Xato: {e}", "ERR")

        log(f"[{split_name}] yozildi: {copied:,}", "OK")

    # ============================================================
    # 4) data.yaml yaratish
    # ============================================================
    yaml_content = f"""# Sergak AI - Sigaret Aniqlash YAKUNIY dataset
# 1 klass: smoking (sigaret chekayotgan odam)
# Avtomatik yaratilgan: final_merge_smoking_v2.py

path: {MERGED_DIR.as_posix()}
train: images/train
val: images/val
test: images/test

nc: 1
names:
  0: smoking
"""
    (MERGED_DIR / "data.yaml").write_text(yaml_content, encoding="utf-8")
    log(f"data.yaml yaratildi", "OK")

    # ============================================================
    # YAKUNIY HISOBOT
    # ============================================================
    header("YAKUNIY NATIJA")

    # Rasm sanash
    final_counts = {}
    for split in ["train", "val", "test"]:
        n = sum(1 for f in (MERGED_DIR / "images" / split).iterdir()
                if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp"))
        final_counts[split] = n

    final_total = sum(final_counts.values())
    print(f"  📁 Joylashish: {MERGED_DIR}")
    print()
    print(f"  📊 Split:")
    print(f"    train: {final_counts['train']:>7,} rasm  ({final_counts['train']*100/final_total:.1f}%)")
    print(f"    val:   {final_counts['val']:>7,} rasm  ({final_counts['val']*100/final_total:.1f}%)")
    print(f"    test:  {final_counts['test']:>7,} rasm  ({final_counts['test']*100/final_total:.1f}%)")
    print(f"    ──────────────────────────")
    print(f"    JAMI:  {final_total:>7,} rasm")
    print()
    print(f"  📊 Bbox:        {total_bbox:>7,} smoking bbox")
    print(f"  📊 O'rtacha:    {total_bbox/final_total:.2f} bbox/rasm")
    print()
    print(f"  📄 data.yaml:   {MERGED_DIR / 'data.yaml'}")
    print()
    print("=" * 72)
    print("  ✅ TRAINING UCHUN TAYYOR!")
    print("=" * 72)
    print()
    print(f"  Klasslar:  1 (smoking)")
    print(f"  Rasmlar:   {final_total:,}")
    print(f"  Bbox:      {total_bbox:,}")
    print()
    print("  Endi training boshlash uchun: train_smoking.py")
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
