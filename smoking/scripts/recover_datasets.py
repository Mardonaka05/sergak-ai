"""
SERGAK AI - YO'QOLGAN DATASETLARNI TIKLASH
=============================================
14,000+ rasm yo'qoldi! Bularni qaytadan yuklab olamiz.

Manbalar (TASDIQLANGAN - oldingi sessiyada ishlagan):
  - Kaggle: 2 ta dataset (~10,000 rasm)
  - Mendeley: 3 ta dataset (~4,000 rasm)
"""
import os
import sys
import subprocess
import time
import zipfile
import shutil
from pathlib import Path

PROJECT_ROOT = Path(r"E:\sergak_smoking")
DATASETS_DIR = PROJECT_ROOT / "datasets"

KAGGLE_TOKEN = os.environ.get("KAGGLE_API_TOKEN", "KGAT_7f6d388560bec29c6ac64aeb06cc09e5")

if not Path("E:\\").exists():
    PROJECT_ROOT = Path(r"D:\sergak dasturi\smoking")
    DATASETS_DIR = PROJECT_ROOT / "datasets"

DATASETS_DIR.mkdir(parents=True, exist_ok=True)


def log(msg, lvl="INFO"):
    symbols = {"INFO": "[i]", "OK": "[+]", "WARN": "[!]", "ERR": "[X]",
               "SKIP": "[-]", "DOWN": "[v]"}
    print(f"  {symbols.get(lvl, '[?]')} {msg}")


def ensure_package(package, import_name=None):
    import_name = import_name or package
    try:
        __import__(import_name)
        return True
    except ImportError:
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", package, "-q"],
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            return False


def count_images(directory):
    if not directory.exists():
        return 0
    try:
        return sum(1 for f in directory.rglob("*")
                   if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp", ".webp"))
    except Exception:
        return 0


# ============================================================
# KAGGLE
# ============================================================
KAGGLE_DATASETS = [
    "muhammetzahitaydn/cigarette-smoker-dataset",                # 9,004 rasm
    "prajjwalkumarpanzade/smoking-and-drinking-dataset-for-yolo", # 1,030 rasm
]


def download_kaggle():
    print()
    print("=" * 70)
    print("  KAGGLE - 2 ta dataset (~10,000 rasm)")
    print("=" * 70)

    # Kaggle token
    access_token_file = Path.home() / ".kaggle" / "access_token"
    if KAGGLE_TOKEN and not access_token_file.exists():
        access_token_file.parent.mkdir(parents=True, exist_ok=True)
        access_token_file.write_text(KAGGLE_TOKEN)

    if not ensure_package("kaggle"):
        return 0

    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        api = KaggleApi()
        api.authenticate()
        log("Kaggle API ulandi", "OK")
    except Exception as e:
        log(f"Auth xato: {e}", "ERR")
        return 0

    total = 0
    for ds_id in KAGGLE_DATASETS:
        name = ds_id.split("/")[-1].replace("-", "_")
        target = DATASETS_DIR / f"kgl_{name}"
        print()
        log(f"[1] {ds_id}", "DOWN")

        if target.exists() and count_images(target) > 100:
            log(f"Mavjud - {count_images(target):,} rasm", "SKIP")
            total += count_images(target)
            continue

        target.mkdir(parents=True, exist_ok=True)
        try:
            api.dataset_download_files(ds_id, path=str(target), unzip=True, quiet=False)
            n = count_images(target)
            total += n
            log(f"OK - {n:,} rasm", "OK")
        except Exception as e:
            log(f"Xato: {str(e)[:120]}", "ERR")

    return total


# ============================================================
# MENDELEY
# ============================================================
MENDELEY_DATASETS = [
    {"name": "smoker_detection",     "id": "j45dj8bgfc", "version": 1},
    {"name": "cigdet",               "id": "6hyrr8typ7", "version": 1},
    {"name": "smoking_not_smoking",  "id": "7b52hhzs3r", "version": 1},
]


def download_mendeley():
    print()
    print("=" * 70)
    print("  MENDELEY - 3 ta dataset (~4,000 rasm)")
    print("=" * 70)

    if not ensure_package("requests"):
        return 0
    if not ensure_package("tqdm"):
        return 0

    import requests
    from tqdm import tqdm

    total = 0
    for i, ds in enumerate(MENDELEY_DATASETS, 1):
        target = DATASETS_DIR / f"mnd_{ds['name']}"
        print()
        log(f"[{i}] {ds['name']}", "DOWN")

        if target.exists() and count_images(target) > 100:
            log(f"Mavjud - {count_images(target):,} rasm", "SKIP")
            total += count_images(target)
            continue

        api_url = f"https://data.mendeley.com/public-api/datasets/{ds['id']}/files?folder_id=root&version={ds['version']}"

        try:
            r = requests.get(api_url, timeout=30)
            if r.status_code != 200:
                log(f"API xato {r.status_code}", "ERR")
                continue

            files = r.json()
            target.mkdir(parents=True, exist_ok=True)

            for f in files:
                file_name = f.get("filename", "unknown")
                file_url = (f.get("content_details", {}).get("download_url")
                            or f.get("download_url"))
                if not file_url:
                    continue

                log(f"Yuklab olinmoqda: {file_name}", "DOWN")
                resp = requests.get(file_url, stream=True, timeout=300)
                total_size = int(resp.headers.get("content-length", 0))
                local_path = target / file_name

                with open(local_path, "wb") as out:
                    with tqdm(total=total_size, unit="B", unit_scale=True, desc=file_name[:30]) as pbar:
                        for chunk in resp.iter_content(chunk_size=8192):
                            if chunk:
                                out.write(chunk)
                                pbar.update(len(chunk))

                # Extract
                if file_name.lower().endswith(".zip"):
                    try:
                        with zipfile.ZipFile(str(local_path)) as zf:
                            zf.extractall(str(target))
                        local_path.unlink()
                    except Exception:
                        pass

            n = count_images(target)
            total += n
            log(f"OK - {n:,} rasm", "OK")

        except Exception as e:
            log(f"Xato: {str(e)[:120]}", "ERR")

    return total


# ============================================================
# MAIN
# ============================================================
def main():
    print()
    print("=" * 70)
    print("  SERGAK AI - YO'QOLGAN DATASETLARNI TIKLASH")
    print("=" * 70)
    print(f"  Manzil: {DATASETS_DIR}")
    print()

    start_time = time.time()

    kgl_imgs = download_kaggle()
    mnd_imgs = download_mendeley()

    elapsed = time.time() - start_time

    print()
    print("=" * 70)
    print("  YAKUNIY HISOBOT")
    print("=" * 70)
    print(f"  Kaggle:    {kgl_imgs:>6,} rasm")
    print(f"  Mendeley:  {mnd_imgs:>6,} rasm")
    print(f"  Vaqt:      {elapsed/60:.1f} daqiqa")
    print()

    print("  Barcha datasetlar:")
    grand = 0
    for d in sorted(DATASETS_DIR.iterdir()):
        if d.is_dir():
            n = count_images(d)
            if n > 0:
                grand += n
                print(f"    {d.name:<50s}  {n:>7,} rasm")

    print()
    print(f"  GRAND TOTAL: {grand:,} rasm")
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
