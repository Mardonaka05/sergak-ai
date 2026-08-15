"""
SERGAK AI - SIGARET EMAS DATASETLARNI O'CHIRISH
=================================================
Faqat haqiqiy SMOKING (sigaret chekayotgan odam) datasetlarini saqlaymiz.
Hammasi: smoke, fire, indoor_smoke, kichik gh_* — O'CHIRILADI.
"""
from pathlib import Path
import shutil

DATASETS_DIR = Path(r"E:\sergak_smoking\datasets")
if not Path("E:\\").exists():
    DATASETS_DIR = Path(r"D:\sergak dasturi\smoking\datasets")


def log(msg, lvl="INFO"):
    symbols = {"INFO": "[i]", "OK": "[+]", "DEL": "[X]", "KEEP": "[✓]", "MISS": "[?]"}
    print(f"  {symbols.get(lvl, '[?]')} {msg}")


def count_images(directory):
    if not directory.exists():
        return 0
    return sum(1 for f in directory.rglob("*")
               if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp", ".webp"))


def get_size_mb(directory):
    if not directory.exists():
        return 0
    return sum(f.stat().st_size for f in directory.rglob("*") if f.is_file()) / 1e6


# ============================================================
# O'CHIRILADIGAN — sigaret emas (smoke/fire/junk)
# ============================================================
DELETE_DATASETS = [
    # Smoke/fire datasetlari (sigaret emas)
    "gh_smoke_abonia",          # Fire + smoke
    "gh_smoke_mnusrat",         # smoke + fire
    "hf_smoke_kerem",           # smoke detection (yong'in)
    "znd_indoor_smoke",         # indoor smoke (yong'in)

    # Juda kichik (faqat kod, real rasm yo'q)
    "gh_smoking_aarno",         # 3 rasm (faqat assets)
    "gh_smoking_alihassan",     # 3 rasm
    "gh_smoking_mehul",         # 4 rasm
    "gh_smoking_richardo",      # 5 rasm
    "gh_smoking_teguh",         # 0 rasm
    "gh_smoking_meera",         # 9 rasm (juda kam)

    # Failed downloads (227KB HTML response, rasm emas)
    "icv_cigarette",
    "icv_smoker",
    "icv_smoking",
]

# ============================================================
# SAQLANADIGAN — haqiqiy smoking person datasetlari
# ============================================================
KEEP_DATASETS = [
    "kgl_cigarette_smoker_dataset",            # 9,004 - folder smoking/not_smoking
    "kgl_smoking_and_drinking_dataset_for_yolo", # 1,030 - YOLO smoking class
    "mnd_smoking_not_smoking",                  # 2,410 - filename based
    "mnd_smoker_detection",                     # 1,120 - filename based
    "mnd_cigdet",                               # 557 - cigarette object
]


def main():
    print()
    print("=" * 72)
    print("  🧹 SERGAK AI - DATASETLARNI TOZALASH (faqat SMOKING saqlash)")
    print("=" * 72)
    print(f"  📁 {DATASETS_DIR}")
    print()

    if not DATASETS_DIR.exists():
        print(f"[X] Topilmadi: {DATASETS_DIR}")
        return

    # AVVAL HOLAT
    print("=" * 72)
    print("  📊 AVVAL HOLAT")
    print("=" * 72)
    total_before = 0
    size_before = 0
    for d in sorted(DATASETS_DIR.iterdir()):
        if d.is_dir():
            n = count_images(d)
            s = get_size_mb(d)
            total_before += n
            size_before += s
            print(f"    {d.name:<45s}  {n:>7,} rasm  {s:>8.1f} MB")

    print(f"  ─────────────────────────────────────────")
    print(f"    JAMI:                                   {total_before:>7,} rasm  {size_before:>8.1f} MB")
    print()

    # O'CHIRISH
    print("=" * 72)
    print("  🗑️  O'CHIRILMOQDA (sigaret emas)")
    print("=" * 72)
    deleted_total = 0
    deleted_size = 0
    for name in DELETE_DATASETS:
        ds_dir = DATASETS_DIR / name
        if ds_dir.exists():
            n = count_images(ds_dir)
            s = get_size_mb(ds_dir)
            deleted_total += n
            deleted_size += s
            try:
                shutil.rmtree(ds_dir)
                log(f"O'chirildi: {name:<35s}  ({n:>6,} rasm, {s:>6.1f} MB)", "DEL")
            except Exception as e:
                log(f"Xato: {name} — {e}", "ERR")
        else:
            log(f"Topilmadi: {name}", "MISS")

    print()
    print(f"  📊 O'chirildi: {deleted_total:,} rasm, {deleted_size:.1f} MB")
    print()

    # SAQLANGAN
    print("=" * 72)
    print("  ✅ SAQLANGAN — faqat SMOKING datasetlari")
    print("=" * 72)
    kept_total = 0
    kept_size = 0
    for name in KEEP_DATASETS:
        ds_dir = DATASETS_DIR / name
        if ds_dir.exists():
            n = count_images(ds_dir)
            s = get_size_mb(ds_dir)
            kept_total += n
            kept_size += s
            log(f"Saqlandi: {name:<45s}  {n:>6,} rasm  {s:>6.1f} MB", "KEEP")
        else:
            log(f"Topilmadi: {name}", "MISS")

    # Boshqa datasetlar (ro'yxatda yo'q)
    others = []
    for d in sorted(DATASETS_DIR.iterdir()):
        if d.is_dir() and d.name not in KEEP_DATASETS and d.name not in DELETE_DATASETS:
            n = count_images(d)
            if n > 0:
                others.append((d.name, n, get_size_mb(d)))

    if others:
        print()
        print("  ⚠️ BOSHQA datasetlar (ro'yxatga kirmagan):")
        for name, n, s in others:
            log(f"  {name:<45s}  {n:>6,} rasm  {s:>6.1f} MB", "INFO")

    print()
    print("=" * 72)
    print("  📊 YAKUNIY HOLAT")
    print("=" * 72)
    print(f"  Avval:        {total_before:>7,} rasm  {size_before:>8.1f} MB")
    print(f"  O'chirildi:  -{deleted_total:>7,} rasm  {deleted_size:>8.1f} MB")
    print(f"  ─────────────────────────────────────────")
    print(f"  Saqlangan:    {kept_total:>7,} rasm  {kept_size:>8.1f} MB")
    print(f"  Disk tejandi: {deleted_size/1024:.2f} GB")
    print()
    print(f"  🎯 SOF SMOKING DATA: {kept_total:,} rasm (training uchun yetarli)")
    print()
    print("=" * 72)
    print("  ⚡ KEYINGI QADAM")
    print("=" * 72)
    print()
    print("  1. Namunalarni qayta tekshirish:")
    print("     .\\11_deep_inspect.bat")
    print()
    print("  2. Konvertatsiya:")
    print("     .\\10_prepare.bat")
    print()
    print("  3. Hammasi tayyor bo'lgach training:")
    print("     .\\train_smoking.bat (yarataman)")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] To'xtatildi")
    except Exception as e:
        print(f"\n[X] XATO: {e}")
