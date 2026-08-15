"""
SERGAK AI - GitHub + Mendeley + Zenodo Avtomatik Yuklab Olish
==============================================================
Roboflow blok qilingan, biz BOSHQA manbalarga o'tdik.

Manbalar:
  - Mendeley Data (public datasets - bemalol yuklab olinadi)
  - Zenodo (open access akademik datasetlar)
  - GitHub (open source repolar)
"""
import os
import sys
import shutil
import subprocess
import time
import zipfile
import io
from pathlib import Path

# ============================================================
PROJECT_ROOT = Path(r"E:\sergak_smoking")
DATASETS_DIR = PROJECT_ROOT / "datasets"

if not Path("E:\\").exists():
    PROJECT_ROOT = Path(r"D:\sergak dasturi\smoking")
    DATASETS_DIR = PROJECT_ROOT / "datasets"

DATASETS_DIR.mkdir(parents=True, exist_ok=True)


def log(msg, lvl="INFO"):
    symbols = {"INFO": "[i]", "OK": "[+]", "WARN": "[!]", "ERR": "[X]", "SKIP": "[-]", "DOWN": "[↓]"}
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
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", package, "-q", "--disable-pip-version-check"],
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            return False


def count_images(directory):
    if not directory.exists():
        return 0
    return sum(1 for f in directory.rglob("*")
               if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp", ".webp"))


# ============================================================
# 🟢 MENDELEY DATA (akademik datasetlar — bemalol)
# ============================================================
MENDELEY_DATASETS = [
    {"name": "smoker_detection",  "id": "j45dj8bgfc", "version": 1,
     "desc": "Smoker Detection — 1120 rasm (560 smoking + 560 not_smoking)"},
    {"name": "cigdet",            "id": "6hyrr8typ7", "version": 1,
     "desc": "CigDet — Sigaret detection"},
    {"name": "smoking_not_smoking", "id": "7b52hhzs3r", "version": 1,
     "desc": "Smoking vs Not-Smoking — 2400 rasm"},
]


def download_mendeley_one(ds_id, version, target_dir):
    """Mendeley public API orqali datasetni yuklab olish."""
    import requests
    from tqdm import tqdm

    # Public API endpoint
    api_url = f"https://data.mendeley.com/public-api/datasets/{ds_id}/files?folder_id=root&version={version}"

    try:
        log(f"API: {api_url}", "INFO")
        r = requests.get(api_url, timeout=30)
        if r.status_code != 200:
            log(f"API xato {r.status_code}", "ERR")
            return False

        files = r.json()
        if not files:
            log("Fayllar topilmadi", "ERR")
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
                resp = requests.get(file_url, stream=True, timeout=180)
                total = int(resp.headers.get("content-length", 0))
                local_path = target_dir / file_name

                with open(local_path, "wb") as out:
                    with tqdm(total=total, unit="B", unit_scale=True, desc=file_name[:30]) as pbar:
                        for chunk in resp.iter_content(chunk_size=8192):
                            if chunk:
                                out.write(chunk)
                                pbar.update(len(chunk))

                # ZIP bo'lsa extract qilish
                if file_name.lower().endswith(".zip"):
                    try:
                        with zipfile.ZipFile(str(local_path), "r") as zf:
                            zf.extractall(str(target_dir))
                        local_path.unlink()  # ZIP ni o'chirish
                        log(f"ZIP extract qilindi", "OK")
                    except Exception as e:
                        log(f"Extract xato: {e}", "WARN")
            except Exception as e:
                log(f"Fayl yuklab olishda xato: {e}", "ERR")
                continue

        return count_images(target_dir) > 0
    except Exception as e:
        log(f"Xato: {e}", "ERR")
        return False


def download_mendeley_all():
    header("🟢 MENDELEY DATA datasetlari")

    if not ensure_package("requests"):
        return 0, 0
    if not ensure_package("tqdm"):
        return 0, 0

    success = 0
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
            success += 1
            total_images += imgs
        else:
            log("Muvaffaqiyatsiz", "ERR")

    return success, total_images


# ============================================================
# 🟢 ZENODO (akademik datasetlar — bemalol)
# ============================================================
ZENODO_DATASETS = [
    {"name": "indoor_smoke", "record_id": "15826133",
     "desc": "Indoor Fire Smoke — 5000 rasm"},
]


def download_zenodo_one(record_id, target_dir):
    """Zenodo'dan datasetni yuklab olish."""
    import requests
    from tqdm import tqdm

    api_url = f"https://zenodo.org/api/records/{record_id}"

    try:
        log(f"API: {api_url}", "INFO")
        r = requests.get(api_url, timeout=30)
        if r.status_code != 200:
            log(f"API xato {r.status_code}", "ERR")
            return False

        data = r.json()
        files = data.get("files", [])
        if not files:
            log("Fayllar topilmadi", "ERR")
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
                resp = requests.get(file_url, stream=True, timeout=300)
                total = int(resp.headers.get("content-length", file_size))
                local_path = target_dir / file_name

                with open(local_path, "wb") as out:
                    with tqdm(total=total, unit="B", unit_scale=True, desc=file_name[:30]) as pbar:
                        for chunk in resp.iter_content(chunk_size=8192):
                            if chunk:
                                out.write(chunk)
                                pbar.update(len(chunk))

                # ZIP/TAR bo'lsa extract qilish
                if file_name.lower().endswith(".zip"):
                    try:
                        with zipfile.ZipFile(str(local_path), "r") as zf:
                            zf.extractall(str(target_dir))
                        local_path.unlink()
                        log(f"ZIP extract qilindi", "OK")
                    except Exception as e:
                        log(f"Extract xato: {e}", "WARN")
                elif file_name.lower().endswith((".tar", ".tar.gz", ".tgz")):
                    try:
                        import tarfile
                        with tarfile.open(str(local_path)) as tf:
                            tf.extractall(str(target_dir))
                        local_path.unlink()
                        log(f"TAR extract qilindi", "OK")
                    except Exception as e:
                        log(f"Extract xato: {e}", "WARN")
            except Exception as e:
                log(f"Fayl yuklab olishda xato: {e}", "ERR")
                continue

        return count_images(target_dir) > 0
    except Exception as e:
        log(f"Xato: {e}", "ERR")
        return False


def download_zenodo_all():
    header("🟢 ZENODO datasetlari")

    success = 0
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
            success += 1
            total_images += imgs

    return success, total_images


# ============================================================
# 🟢 GITHUB repolari
# ============================================================
GITHUB_REPOS = [
    {"name": "smoking_aarno",      "url": "https://github.com/AarnoStormborn/Smoking-Detection",
     "branch": "main", "desc": "Cigarette Detection Django"},
    {"name": "smoking_meera",      "url": "https://github.com/meerapadmanabhan/Smoking-Detection-Project-Using-Yolov8",
     "branch": "main", "desc": "YOLOv8 smoking detection"},
    {"name": "smoking_mehul",      "url": "https://github.com/mehulpurohit97/Cigarette-Smoking-Detection-using-Deep-Learning",
     "branch": "main", "desc": "Deep Learning smoking"},
    {"name": "smoking_richardo",   "url": "https://github.com/RichardoMrMu/yolov5-smoke-detection-python",
     "branch": "master", "desc": "YOLOv5 smoke detection"},
    {"name": "smoking_alihassan",  "url": "https://github.com/alihassanml/Smoking-detection-yolo11",
     "branch": "main", "desc": "YOLO11 smoking"},
    {"name": "smoke_abonia",       "url": "https://github.com/Abonia1/YOLOv8-Fire-and-Smoke-Detection",
     "branch": "main", "desc": "Fire + smoke detection"},
    {"name": "smoke_mnusrat",      "url": "https://github.com/mnusrat786/smoke-and-fire-detection-",
     "branch": "main", "desc": "Smoke fire detection"},
    {"name": "smoking_teguh",      "url": "https://github.com/teguhsukmanaa/Smoking-Detection-Computer-Vision",
     "branch": "main", "desc": "CV smoking detection"},
]


def download_github_repo(url, branch, target_dir):
    """GitHub repository'ni ZIP sifatida yuklab olish."""
    import requests

    # ZIP URL formati: https://github.com/USER/REPO/archive/refs/heads/BRANCH.zip
    zip_url = f"{url}/archive/refs/heads/{branch}.zip"

    try:
        log(f"ZIP yuklab olinmoqda: {zip_url}", "DOWN")
        r = requests.get(zip_url, stream=True, timeout=180)

        if r.status_code != 200:
            # Boshqa branch'ni sinab ko'rish
            for alt_branch in ["main", "master", "dev", "develop"]:
                if alt_branch == branch:
                    continue
                zip_url2 = f"{url}/archive/refs/heads/{alt_branch}.zip"
                r = requests.get(zip_url2, stream=True, timeout=180)
                if r.status_code == 200:
                    log(f"'{alt_branch}' branch'i topildi", "OK")
                    break
            if r.status_code != 200:
                log(f"HTTP {r.status_code}", "ERR")
                return False

        # ZIP'ni xotirada o'qish va extract qilish
        zip_content = io.BytesIO()
        total = int(r.headers.get("content-length", 0))
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                zip_content.write(chunk)

        target_dir.mkdir(parents=True, exist_ok=True)
        zip_content.seek(0)
        with zipfile.ZipFile(zip_content) as zf:
            zf.extractall(str(target_dir))

        return True
    except Exception as e:
        log(f"Xato: {str(e)[:120]}", "ERR")
        return False


def download_github_all():
    header("🟢 GITHUB repository datasetlari")

    if not ensure_package("requests"):
        return 0, 0

    success = 0
    total_images = 0

    for i, repo in enumerate(GITHUB_REPOS, 1):
        target = DATASETS_DIR / f"gh_{repo['name']}"
        print()
        print(f"  [{i}/{len(GITHUB_REPOS)}] {repo['name']}")
        print(f"        {repo['desc']}")

        if target.exists():
            existing = count_images(target)
            if existing > 50:
                log(f"Mavjud - {existing:,} rasm", "SKIP")
                total_images += existing
                continue
            else:
                shutil.rmtree(target, ignore_errors=True)

        if download_github_repo(repo["url"], repo["branch"], target):
            imgs = count_images(target)
            if imgs > 0:
                log(f"OK - {imgs:,} rasm", "OK")
                success += 1
                total_images += imgs
            else:
                log("Yuklab olindi, lekin rasm yo'q (faqat kod)", "WARN")

    return success, total_images


# ============================================================
# MAIN
# ============================================================
def main():
    print()
    print("=" * 72)
    print("  SERGAK AI - GITHUB + MENDELEY + ZENODO YUKLAB OLISH")
    print("=" * 72)
    print(f"  Manzil: {DATASETS_DIR}")
    print(f"  Reja: 3 Mendeley + 1 Zenodo + 8 GitHub = 12 manba")
    print()

    start_time = time.time()

    mnd_count, mnd_imgs = download_mendeley_all()
    znd_count, znd_imgs = download_zenodo_all()
    gh_count, gh_imgs = download_github_all()

    elapsed = time.time() - start_time

    # YAKUNIY HISOBOT
    header("YAKUNIY HISOBOT (yangi)")

    new_imgs = mnd_imgs + znd_imgs + gh_imgs

    # Eski (HF + Kaggle) sanash
    old_imgs = 0
    for d in DATASETS_DIR.iterdir():
        if d.is_dir() and not d.name.startswith(("mnd_", "znd_", "gh_")):
            old_imgs += count_images(d)

    total_imgs = new_imgs + old_imgs
    total_size = sum(f.stat().st_size for f in DATASETS_DIR.rglob("*") if f.is_file())

    print(f"  📦 Mendeley:        {mnd_count} dataset, {mnd_imgs:>7,} rasm")
    print(f"  📦 Zenodo:          {znd_count} dataset, {znd_imgs:>7,} rasm")
    print(f"  📦 GitHub:          {gh_count} dataset, {gh_imgs:>7,} rasm")
    print(f"  ─────────────────────────────────────")
    print(f"  📊 YANGI:           {mnd_count+znd_count+gh_count} dataset, {new_imgs:>7,} rasm")
    print(f"  📊 ESKI (HF+Kgl):   {old_imgs:>7,} rasm")
    print(f"  📊 JAMI HOZIR:      {total_imgs:>7,} rasm")
    print(f"  💾 Disk:            {total_size/1e9:.2f} GB")
    print(f"  ⏱️  Vaqt:            {elapsed/60:.1f} daqiqa")
    print()

    # Hammasini ko'rsatish
    print("  📁 Barcha datasetlar:")
    for d in sorted(DATASETS_DIR.iterdir()):
        if d.is_dir():
            n = count_images(d)
            if n > 0:
                size_mb = sum(f.stat().st_size for f in d.rglob("*") if f.is_file()) / 1e6
                print(f"    ✅ {d.name:<45s}  {n:>7,} rasm   {size_mb:>7.1f} MB")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] To'xtatildi (Ctrl+C)")
    except Exception as e:
        print(f"\n[X] XATO: {e}")
        import traceback
        traceback.print_exc()
