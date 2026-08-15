"""
SERGAK AI - ZIP fayllarni EXTRACT va TASHKILLASHTIRISH
========================================================
E:\\sergak_smoking\\ dan 7 ta Roboflow ZIP fayllarni extract qiladi
D:\\sergak dasturi\\sergak_smoking\\datasets\\ ga ko'chiradi
Junk fayllarni tozalaydi (znd_indoor_smoke, gh_*)
"""
from pathlib import Path
import zipfile
import shutil
import time

SOURCE_DIR = Path(r"E:\sergak_smoking")
TARGET_DIR = Path(r"D:\sergak dasturi\sergak_smoking")
TARGET_DATASETS = TARGET_DIR / "datasets"


def log(msg, lvl="INFO"):
    symbols = {"INFO": "[i]", "OK": "[+]", "WARN": "[!]", "ERR": "[X]",
               "SKIP": "[-]", "EXTRACT": "[v]", "MOVE": "[->"}
    print(f"  {symbols.get(lvl, '[?]')} {msg}")


def count_images(directory):
    if not directory.exists():
        return 0
    try:
        return sum(1 for f in directory.rglob("*")
                   if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp", ".webp")
                   and "__MACOSX" not in str(f))
    except Exception:
        return 0


def get_size_mb(p):
    try:
        if p.is_file():
            return p.stat().st_size / 1e6
        return sum(f.stat().st_size for f in p.rglob("*") if f.is_file()) / 1e6
    except Exception:
        return 0


def safe_extract_zip(zip_path, extract_to):
    """ZIP'ni xavfsiz extract qilish (__MACOSX skip)."""
    try:
        with zipfile.ZipFile(str(zip_path), "r") as zf:
            members = [m for m in zf.namelist()
                       if not m.startswith("__MACOSX") and not m.startswith("._")]
            for member in members:
                try:
                    zf.extract(member, str(extract_to))
                except Exception:
                    continue
        return True
    except Exception as e:
        log(f"Extract xato: {e}", "ERR")
        return False


def get_zip_target_name(zip_name):
    """ZIP fayl nomidan papka nomi yaratish."""
    name = zip_name.lower().replace(".zip", "")
    name = name.replace(" ", "_")
    name = name.replace(".yolov8", "")
    name = name.replace(".v1i", "_v1").replace(".v2i", "_v2").replace(".v3i", "_v3")
    name = name.replace(".v5i", "_v5")
    name = name.replace(".v1-smoker1", "_smoker1")
    return f"rbf_{name}"


def main():
    print()
    print("=" * 72)
    print("  SERGAK AI - ZIP EXTRACT va TASHKILLASHTIRISH")
    print("=" * 72)
    print(f"  Source:  {SOURCE_DIR}")
    print(f"  Target:  {TARGET_DATASETS}")
    print()

    if not SOURCE_DIR.exists():
        print(f"[X] Source topilmadi: {SOURCE_DIR}")
        return

    # Target papka yaratish
    TARGET_DATASETS.mkdir(parents=True, exist_ok=True)

    # ============================================================
    # 1) BARCHA ZIP FAYLLARNI EXTRACT QILISH
    # ============================================================
    print("=" * 72)
    print("  1) ZIP fayllarni EXTRACT qilish")
    print("=" * 72)

    zip_files = sorted(SOURCE_DIR.glob("*.zip"))
    log(f"Topildi: {len(zip_files)} ta ZIP fayl", "INFO")

    total_extracted = 0
    for zip_path in zip_files:
        size_mb = get_size_mb(zip_path)
        target_name = get_zip_target_name(zip_path.name)
        target_path = TARGET_DATASETS / target_name

        print()
        log(f"{zip_path.name}  ({size_mb:.1f} MB)", "EXTRACT")
        log(f"  -> {target_name}", "INFO")

        if target_path.exists() and count_images(target_path) > 50:
            log(f"  Allaqachon extract qilingan ({count_images(target_path):,} rasm)", "SKIP")
            total_extracted += count_images(target_path)
            continue

        # Eski papkani tozalash
        if target_path.exists():
            try:
                shutil.rmtree(target_path)
            except Exception:
                pass

        if safe_extract_zip(zip_path, target_path):
            imgs = count_images(target_path)
            log(f"  Extract qilindi: {imgs:,} rasm", "OK")
            total_extracted += imgs
        else:
            log(f"  Extract xato!", "ERR")

    # ============================================================
    # 2) MAVJUD DATASETLARNI KO'CHIRISH
    # ============================================================
    print()
    print("=" * 72)
    print("  2) MAVJUD datasetlarni ko'chirish (Smoking-CCTV va h.k.)")
    print("=" * 72)

    source_datasets = SOURCE_DIR / "datasets"
    if source_datasets.exists():
        for d in source_datasets.iterdir():
            if not d.is_dir():
                continue

            # Junk papkalarni skip qilish
            name_lower = d.name.lower()
            is_junk = (
                "macosx" in name_lower or
                d.name.startswith("gh_smoking_") or  # Faqat kod
                d.name == "znd_indoor_smoke"          # Yong'in, sigaret emas
            )

            if is_junk:
                log(f"SKIP (junk): {d.name}", "SKIP")
                continue

            # Yaxshi datasetni ko'chirish
            n = count_images(d)
            if n == 0:
                log(f"SKIP (bo'sh): {d.name}", "SKIP")
                continue

            dst_name = d.name.replace(".v1i.yolov8", "_v1")
            dst = TARGET_DATASETS / dst_name

            if dst.exists() and count_images(dst) > 0:
                log(f"SKIP (mavjud): {dst_name}", "SKIP")
                continue

            try:
                shutil.copytree(str(d), str(dst))
                log(f"Ko'chirildi: {dst_name} ({n:,} rasm)", "OK")
            except Exception as e:
                log(f"Xato: {e}", "ERR")
    else:
        log("Source datasets papkasi yo'q", "WARN")

    # ============================================================
    # YAKUNIY HISOBOT
    # ============================================================
    print()
    print("=" * 72)
    print("  YAKUNIY HISOBOT")
    print("=" * 72)

    grand_total = 0
    grand_size = 0
    print()
    print("  D:\\sergak dasturi\\sergak_smoking\\datasets\\ ichidagi datasetlar:")
    print()

    for d in sorted(TARGET_DATASETS.iterdir()):
        if d.is_dir():
            n = count_images(d)
            s = get_size_mb(d)
            grand_total += n
            grand_size += s
            print(f"    {d.name:<55s}  {n:>7,} rasm  {s:>8.1f} MB")

    print()
    print(f"  JAMI: {grand_total:,} rasm  ({grand_size/1024:.2f} GB)")
    print()
    print("=" * 72)
    print("  KEYINGI QADAM:")
    print("=" * 72)
    print()
    print("  1. Tekshirish (HTML hisobot):")
    print("       cd D:\\sergak dasturi\\smoking")
    print("       .\\13_ideal_inspect_new.bat")
    print()
    print("  2. Konvertatsiya:")
    print("       .\\10_prepare_new.bat")
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
