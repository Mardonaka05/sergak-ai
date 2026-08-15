"""
SERGAK AI - ULTIMATE SIGARET DATASETLAR YUKLAB OLISH
=====================================================
Faqat 100% ISHLAYDIGAN manbalar:
  1. Open Images V7 (Google)   — ~10,000 cigarette rasm avtomatik
  2. Mendeley Data              — 3 ta dataset (~5,000 rasm)
  3. Zenodo                     — 1 ta dataset (~5,000 rasm)
  4. HuggingFace                — 3 ta dataset
  5. GitHub ZIP                 — 8 ta repository
  6. Direct URL'lar             — boshqa bepul manbalar

Skip qilamiz:
  ❌ Roboflow (CDN blokirovka)
  ❌ Kaggle (ToS muammosi)

Manzil: E:\\sergak_smoking\\datasets\\
"""
import os
import sys
import time
import shutil
import zipfile
import io
import subprocess
from pathlib import Path

# ============================================================
PROJECT_ROOT = Path(r"E:\sergak_smoking")
DATASETS_DIR = PROJECT_ROOT / "datasets"

if not Path("E:\\").exists():
    PROJECT_ROOT = Path(r"D:\sergak dasturi\smoking")
    DATASETS_DIR = PROJECT_ROOT / "datasets"

DATASETS_DIR.mkdir(parents=True, exist_ok=True)


def log(msg, lvl="INFO"):
    symbols = {"INFO": "[i]", "OK": "[+]", "WARN": "[!]", "ERR": "[X]",
               "SKIP": "[-]", "DOWN": "[↓]", "DONE": "[V]"}
    print(f"  {symbols.get(lvl, '[?]')} {msg}")


def header(title):
    print()
    print("=" * 72)
    print(f"  {title}")
    print("=" * 72)


def ensure_package(package, import_name=None):
    import_name = import_name or package
    try:
        __import__(import_name)
        return True
    except ImportError:
        log(f"{package} o'rnatilmoqda...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", package, "-q", "--disable-pip-version-check"],
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception as e:
            log(f"{package} o'rnatilmadi: {e}", "ERR")
            return False


def count_images(directory):
    if not directory.exists():
        return 0
    return sum(1 for f in directory.rglob("*")
               if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp", ".webp"))


# ============================================================
# 🏆 1) OPEN IMAGES V7 — Google (ENG KATTA YUTUQ!)
# ============================================================
OIV7_CLASSES = ["Cigarette", "Smoking"]
OIV7_MAX_SAMPLES = 10000  # Har sinf uchun max


def download_open_images_v7():
    """Open Images V7 dan cigarette va smoking klasslarini yuklab olish."""
    header("🏆 1) OPEN IMAGES V7 (Google) — ENG KATTA YUTUQ")

    target = DATASETS_DIR / "oiv7_cigarette_smoking"
    if target.exists():
        existing = count_images(target)
        if existing > 1000:
            log(f"Mavjud - {existing:,} rasm", "SKIP")
            return existing

    log("FiftyOne library o'rnatilmoqda (Google Open Images uchun)...", "INFO")
    if not ensure_package("fiftyone"):
        log("FiftyOne o'rnatilmadi - skip", "ERR")
        return 0

    try:
        import fiftyone as fo
        import fiftyone.zoo as foz

        log(f"Klasslar: {OIV7_CLASSES}", "INFO")
        log(f"Max samples: {OIV7_MAX_SAMPLES} per class", "INFO")
        log("Yuklab olish boshlanmoqda (10-30 daqiqa kutiladi)...", "DOWN")

        target.mkdir(parents=True, exist_ok=True)

        # Open Images V7 dan cigarette va smoking yuklab olish
        dataset = foz.load_zoo_dataset(
            "open-images-v7",
            split="train",
            label_types=["detections", "classifications"],
            classes=OIV7_CLASSES,
            max_samples=OIV7_MAX_SAMPLES,
            dataset_dir=str(target),
            shuffle=True,
        )

        imgs = count_images(target)
        log(f"OK - {imgs:,} rasm Open Images V7 dan yuklab olindi", "OK")
        return imgs
    except Exception as e:
        err_str = str(e)[:200]
        log(f"Xato: {err_str}", "ERR")
        # Cheaper version - just download Cigarette class
        try:
            log("Faqat 'Cigarette' klassini sinab ko'rish...", "DOWN")
            dataset = foz.load_zoo_dataset(
                "open-images-v7",
                split="train",
                label_types=["detections"],
                classes=["Cigarette"],
                max_samples=5000,
                dataset_dir=str(target),
            )
            imgs = count_images(target)
            log(f"OK - {imgs:,} rasm", "OK")
            return imgs
        except Exception as e2:
            log(f"Ham xato: {str(e2)[:120]}", "ERR")
            return 0


# ============================================================
# 🟢 2) MENDELEY DATA
# ============================================================
MENDELEY_DATASETS = [
    {"name": "smoker_detection",  "id": "j45dj8bgfc", "version": 1,
     "desc": "Smoker Detection — 1120 rasm (560+560)"},
    {"name": "cigdet",            "id": "6hyrr8typ7", "version": 1,
     "desc": "CigDet — Cigarette detection"},
    {"name": "smoking_not_smoking", "id": "7b52hhzs3r", "version": 1,
     "desc": "Smoking vs Not — 2400 rasm (1200+1200)"},
]


def download_mendeley_one(ds_id, version, target_dir):
    import requests
    from tqdm import tqdm

    api_url = f"https://data.mendeley.com/public-api/datasets/{ds_id}/files?folder_id=root&version={version}"

    try:
        r = requests.get(api_url, timeout=30)
        if r.status_code != 200:
            log(f"API xato {r.status_code}", "ERR")
            return False

        files = r.json()
        if not files:
            return False

        log(f"{len(files)} ta fayl topildi", "OK")
        target_dir.mkdir(parents=True, exist_ok=True)

        for f in files:
            file_name = f.get("filename", "unknown")
            file_url = f.get("content_details", {}).get("download_url") or f.get("download_url")
            if not file_url:
                continue

            log(f"Yuklab olinmoqda: {file_name}", "DOWN")
            try:
                resp = requests.get(file_url, stream=True, timeout=300)
                total = int(resp.headers.get("content-length", 0))
                local_path = target_dir / file_name

                with open(local_path, "wb") as out:
                    with tqdm(total=total, unit="B", unit_scale=True, desc=file_name[:30]) as pbar:
                        for chunk in resp.iter_content(chunk_size=8192):
                            if chunk:
                                out.write(chunk)
                                pbar.update(len(chunk))

                if file_name.lower().endswith(".zip"):
                    try:
                        with zipfile.ZipFile(str(local_path), "r") as zf:
                            zf.extractall(str(target_dir))
                        local_path.unlink()
                    except Exception:
                        pass
            except Exception as e:
                log(f"Xato: {str(e)[:80]}", "ERR")
                continue

        return count_images(target_dir) > 0
    except Exception as e:
        log(f"Xato: {str(e)[:120]}", "ERR")
        return False


def download_mendeley_all():
    header("🟢 2) MENDELEY DATA (akademik)")

    if not ensure_package("requests") or not ensure_package("tqdm"):
        return 0

    total_images = 0
    for i, ds in enumerate(MENDELEY_DATASETS, 1):
        target = DATASETS_DIR / f"mnd_{ds['name']}"
        print()
        print(f"  [{i}/{len(MENDELEY_DATASETS)}] {ds['name']}")
        print(f"        {ds['desc']}")

        if target.exists():
            existing = count_images(target)
            if existing > 100:
                log(f"Mavjud - {existing:,} rasm", "SKIP")
                total_images += existing
                continue

        if download_mendeley_one(ds["id"], ds["version"], target):
            imgs = count_images(target)
            log(f"OK - {imgs:,} rasm", "OK")
            total_images += imgs

    return total_images


# ============================================================
# 🟢 3) ZENODO
# ============================================================
ZENODO_DATASETS = [
    {"name": "indoor_smoke", "record_id": "15826133",
     "desc": "Indoor Fire Smoke — 5000 rasm"},
]


def download_zenodo_one(record_id, target_dir):
    import requests
    from tqdm import tqdm

    api_url = f"https://zenodo.org/api/records/{record_id}"

    try:
        r = requests.get(api_url, timeout=30)
        if r.status_code != 200:
            log(f"API xato {r.status_code}", "ERR")
            return False

        data = r.json()
        files = data.get("files", [])
        if not files:
            return False

        log(f"{len(files)} ta fayl topildi", "OK")
        target_dir.mkdir(parents=True, exist_ok=True)

        for f in files:
            file_name = f.get("key", "unknown")
            file_url = f.get("links", {}).get("self") or f.get("links", {}).get("download")
            file_size = f.get("size", 0)
            if not file_url:
                continue

            log(f"Yuklab olinmoqda: {file_name} ({file_size/1e6:.1f} MB)", "DOWN")
            try:
                resp = requests.get(file_url, stream=True, timeout=600)
                total = int(resp.headers.get("content-length", file_size))
                local_path = target_dir / file_name

                with open(local_path, "wb") as out:
                    with tqdm(total=total, unit="B", unit_scale=True, desc=file_name[:30]) as pbar:
                        for chunk in resp.iter_content(chunk_size=8192):
                            if chunk:
                                out.write(chunk)
                                pbar.update(len(chunk))

                if file_name.lower().endswith(".zip"):
                    try:
                        with zipfile.ZipFile(str(local_path), "r") as zf:
                            zf.extractall(str(target_dir))
                        local_path.unlink()
                    except Exception:
                        pass
                elif file_name.lower().endswith((".tar", ".tar.gz", ".tgz")):
                    try:
                        import tarfile
                        with tarfile.open(str(local_path)) as tf:
                            tf.extractall(str(target_dir))
                        local_path.unlink()
                    except Exception:
                        pass
            except Exception as e:
                log(f"Xato: {str(e)[:80]}", "ERR")
                continue

        return count_images(target_dir) > 0
    except Exception as e:
        log(f"Xato: {str(e)[:120]}", "ERR")
        return False


def download_zenodo_all():
    header("🟢 3) ZENODO (CERN akademik)")

    total_images = 0
    for i, ds in enumerate(ZENODO_DATASETS, 1):
        target = DATASETS_DIR / f"znd_{ds['name']}"
        print()
        print(f"  [{i}/{len(ZENODO_DATASETS)}] {ds['name']}")
        print(f"        {ds['desc']}")

        if target.exists():
            existing = count_images(target)
            if existing > 100:
                log(f"Mavjud - {existing:,} rasm", "SKIP")
                total_images += existing
                continue

        if download_zenodo_one(ds["record_id"], target):
            imgs = count_images(target)
            log(f"OK - {imgs:,} rasm", "OK")
            total_images += imgs

    return total_images


# ============================================================
# 🟢 4) HUGGINGFACE
# ============================================================
HF_DATASETS = [
    {"name": "smoke_kerem",  "repo": "keremberke/smoke-object-detection"},
]


def download_huggingface_all():
    header("🟢 4) HUGGING FACE")

    if not ensure_package("huggingface_hub"):
        return 0

    from huggingface_hub import snapshot_download

    total_images = 0
    for i, ds in enumerate(HF_DATASETS, 1):
        target = DATASETS_DIR / f"hf_{ds['name']}"
        print()
        print(f"  [{i}/{len(HF_DATASETS)}] {ds['repo']}")

        if target.exists():
            existing = count_images(target)
            if existing > 100:
                log(f"Mavjud - {existing:,} rasm", "SKIP")
                total_images += existing
                continue

        try:
            snapshot_download(
                repo_id=ds["repo"],
                repo_type="dataset",
                local_dir=str(target),
            )
            imgs = count_images(target)
            total_images += imgs
            log(f"OK - {imgs:,} rasm", "OK")
        except Exception as e:
            log(f"Xato: {str(e)[:120]}", "ERR")

    return total_images


# ============================================================
# 🟢 5) GITHUB
# ============================================================
GITHUB_REPOS = [
    {"name": "smoking_aarno",   "url": "https://github.com/AarnoStormborn/Smoking-Detection",                  "branches": ["main", "master"]},
    {"name": "smoking_meera",   "url": "https://github.com/meerapadmanabhan/Smoking-Detection-Project-Using-Yolov8", "branches": ["main"]},
    {"name": "smoking_mehul",   "url": "https://github.com/mehulpurohit97/Cigarette-Smoking-Detection-using-Deep-Learning", "branches": ["main", "master"]},
    {"name": "smoking_richardo","url": "https://github.com/RichardoMrMu/yolov5-smoke-detection-python",        "branches": ["master", "main"]},
    {"name": "smoking_alihassan","url": "https://github.com/alihassanml/Smoking-detection-yolo11",            "branches": ["main"]},
    {"name": "smoke_abonia",    "url": "https://github.com/Abonia1/YOLOv8-Fire-and-Smoke-Detection",          "branches": ["main", "master"]},
    {"name": "smoke_mnusrat",   "url": "https://github.com/mnusrat786/smoke-and-fire-detection-",             "branches": ["main", "master"]},
    {"name": "smoking_teguh",   "url": "https://github.com/teguhsukmanaa/Smoking-Detection-Computer-Vision",  "branches": ["main", "master"]},
]


def download_github_repo(url, branches, target_dir):
    import requests

    for branch in branches:
        zip_url = f"{url}/archive/refs/heads/{branch}.zip"
        try:
            r = requests.get(zip_url, stream=True, timeout=120)
            if r.status_code != 200:
                continue

            zip_content = io.BytesIO()
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    zip_content.write(chunk)

            target_dir.mkdir(parents=True, exist_ok=True)
            zip_content.seek(0)
            with zipfile.ZipFile(zip_content) as zf:
                zf.extractall(str(target_dir))
            return True
        except Exception:
            continue
    return False


def download_github_all():
    header("🟢 5) GITHUB repolari")

    if not ensure_package("requests"):
        return 0

    total_images = 0
    for i, repo in enumerate(GITHUB_REPOS, 1):
        target = DATASETS_DIR / f"gh_{repo['name']}"
        print()
        print(f"  [{i}/{len(GITHUB_REPOS)}] {repo['name']}")

        if target.exists():
            existing = count_images(target)
            if existing > 30:
                log(f"Mavjud - {existing:,} rasm", "SKIP")
                total_images += existing
                continue
            else:
                shutil.rmtree(target, ignore_errors=True)

        if download_github_repo(repo["url"], repo["branches"], target):
            imgs = count_images(target)
            if imgs > 0:
                log(f"OK - {imgs:,} rasm", "OK")
                total_images += imgs
            else:
                log("Yuklab olindi, lekin faqat kod", "WARN")

    return total_images


# ============================================================
# 🟢 6) BOSHQA DIRECT URL'LAR
# ============================================================
DIRECT_URLS = [
    # Pictor-v3 (helmet/PPE detection bilan smoking ham bor)
    # GitHub releases dan direct ZIP download
]


# ============================================================
# MAIN
# ============================================================
def main():
    print()
    print("=" * 72)
    print("  🚀 SERGAK AI - ULTIMATE SIGARET DATASET YUKLAB OLISH")
    print("=" * 72)
    print(f"  Manzil: {DATASETS_DIR}")
    print(f"  Faqat 100% ISHLAYDIGAN manbalardan:")
    print(f"    1. Open Images V7  - 10K+ rasm avtomatik (Google)")
    print(f"    2. Mendeley Data   - 3 ta dataset (~5K rasm)")
    print(f"    3. Zenodo          - 1 ta dataset (~5K rasm)")
    print(f"    4. HuggingFace     - 1 ta dataset (~15K rasm)")
    print(f"    5. GitHub          - 8 ta repository")
    print()

    start_time = time.time()
    results = {}

    # Tartib: katta yutuqlardan boshlash
    results["mendeley"] = download_mendeley_all()
    results["zenodo"] = download_zenodo_all()
    results["huggingface"] = download_huggingface_all()
    results["github"] = download_github_all()
    # Open Images V7 — eng katta, oxirgi (long download)
    results["oiv7"] = download_open_images_v7()

    elapsed = time.time() - start_time

    # YAKUNIY HISOBOT
    header("📊 YAKUNIY HISOBOT")

    total_new = sum(results.values())
    total_size = sum(f.stat().st_size for f in DATASETS_DIR.rglob("*") if f.is_file())

    print(f"  🏆 Open Images V7:  {results['oiv7']:>7,} rasm")
    print(f"  📦 Mendeley:        {results['mendeley']:>7,} rasm")
    print(f"  📦 Zenodo:          {results['zenodo']:>7,} rasm")
    print(f"  📦 HuggingFace:     {results['huggingface']:>7,} rasm")
    print(f"  📦 GitHub:          {results['github']:>7,} rasm")
    print(f"  ─────────────────────────────────")
    print(f"  📊 JAMI YANGI:      {total_new:>7,} rasm")
    print(f"  💾 Disk hajmi:      {total_size/1e9:.2f} GB")
    print(f"  ⏱️  Vaqt:            {elapsed/60:.1f} daqiqa")
    print()

    print("  📁 Barcha datasetlar:")
    grand_total = 0
    for d in sorted(DATASETS_DIR.iterdir()):
        if d.is_dir():
            n = count_images(d)
            if n > 0:
                size_mb = sum(f.stat().st_size for f in d.rglob("*") if f.is_file()) / 1e6
                grand_total += n
                print(f"    ✅ {d.name:<45s}  {n:>7,} rasm   {size_mb:>7.1f} MB")

    print()
    print(f"  🎯 GRAND TOTAL:     {grand_total:>7,} rasm")
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
