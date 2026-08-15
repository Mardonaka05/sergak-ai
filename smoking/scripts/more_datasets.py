"""
SERGAK AI - YANGI SIGARET DATASETLAR (10,000+ RASM!)
=====================================================

Avval bo'lmagan YANGI manbalar:
  1. images.cv         - 10,300 rasm (3 ta dataset, ro'yxat shart emas!)
  2. Smoke100k         - 100,000 synthesized smoke rasm
  3. Deep-smoke-machine (CMU)
  4. DFS-FIRE-SMOKE
  5. Yana Mendeley/Zenodo qo'shimcha

Hammasi avtomatik yuklab olinadi (Roboflow/Kaggle SKIP).
"""
import os
import sys
import time
import shutil
import zipfile
import io
import subprocess
import webbrowser
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


def download_url_to_file(url, dest_path, desc="file"):
    """URL'ni faylga yuklab olish."""
    import requests
    from tqdm import tqdm
    try:
        log(f"Yuklab olinmoqda: {desc}", "DOWN")
        r = requests.get(url, stream=True, timeout=300, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        if r.status_code != 200:
            log(f"HTTP {r.status_code}", "ERR")
            return False
        total = int(r.headers.get("content-length", 0))
        with open(dest_path, "wb") as f:
            with tqdm(total=total, unit="B", unit_scale=True, desc=desc[:30]) as pbar:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
        return True
    except Exception as e:
        log(f"Xato: {str(e)[:100]}", "ERR")
        return False


def extract_archive(archive_path, target_dir):
    """ZIP/TAR/RAR ni extract qilish."""
    name = archive_path.name.lower()
    target_dir.mkdir(parents=True, exist_ok=True)
    try:
        if name.endswith(".zip"):
            with zipfile.ZipFile(str(archive_path)) as zf:
                zf.extractall(str(target_dir))
            return True
        elif name.endswith((".tar.gz", ".tgz", ".tar")):
            import tarfile
            with tarfile.open(str(archive_path)) as tf:
                tf.extractall(str(target_dir))
            return True
        elif name.endswith(".rar"):
            # RAR uchun ekstraktsiya
            try:
                import rarfile
                with rarfile.RarFile(str(archive_path)) as rf:
                    rf.extractall(str(target_dir))
                return True
            except ImportError:
                log("rarfile yo'q, pip install rarfile + WinRAR kerak", "WARN")
                return False
            except Exception as e:
                log(f"RAR extract xato: {e}", "ERR")
                return False
    except Exception as e:
        log(f"Extract xato: {e}", "ERR")
        return False


# ============================================================
# 🟢 1) IMAGES.CV — 3 ta dataset (10,300 rasm!)
# ============================================================
# images.cv direct download URL pattern
IMAGES_CV_DATASETS = [
    {
        "name": "smoker",
        "slug": "smoker-image-classification-dataset",
        "url": "https://images.cv/api/v1/datasets/smoker-image-classification-dataset/download",
        "alt_url": "https://images.cv/download/smoker-image-classification-dataset",
        "expected": 1700,
        "desc": "Smoker Image Classification — 1,700 rasm"
    },
    {
        "name": "smoking",
        "slug": "smoking-image-classification-dataset",
        "url": "https://images.cv/api/v1/datasets/smoking-image-classification-dataset/download",
        "alt_url": "https://images.cv/download/smoking-image-classification-dataset",
        "expected": 6900,
        "desc": "Smoking Image Classification — 6,900 rasm (KATTA!)"
    },
    {
        "name": "cigarette",
        "slug": "cigarette-image-classification-dataset",
        "url": "https://images.cv/api/v1/datasets/cigarette-image-classification-dataset/download",
        "alt_url": "https://images.cv/download/cigarette-image-classification-dataset",
        "expected": 1700,
        "desc": "Cigarette Labeled — 1,700 rasm"
    },
]


def download_images_cv():
    header("🟢 1) IMAGES.CV — 3 ta YANGI dataset (10,300 rasm)")

    if not ensure_package("requests"):
        return 0

    total_imgs = 0
    failed_manual = []

    for i, ds in enumerate(IMAGES_CV_DATASETS, 1):
        target = DATASETS_DIR / f"icv_{ds['name']}"
        zip_path = DATASETS_DIR / f"icv_{ds['name']}.zip"
        print()
        print(f"  [{i}/{len(IMAGES_CV_DATASETS)}] {ds['name']}")
        print(f"        {ds['desc']}")

        if target.exists() and count_images(target) > 100:
            log(f"Mavjud - {count_images(target):,} rasm", "SKIP")
            total_imgs += count_images(target)
            continue

        # Bir nechta URL'larni sinab ko'rish
        success = False
        for url in [ds["url"], ds["alt_url"]]:
            if download_url_to_file(url, zip_path, ds["name"]):
                if zip_path.stat().st_size > 100000:  # 100KB dan katta
                    if extract_archive(zip_path, target):
                        zip_path.unlink()
                        imgs = count_images(target)
                        if imgs > 0:
                            log(f"OK - {imgs:,} rasm", "OK")
                            total_imgs += imgs
                            success = True
                            break

        if not success:
            failed_manual.append(ds)
            try:
                if zip_path.exists():
                    zip_path.unlink()
            except Exception:
                pass

    # Qo'lda yuklab olish ko'rsatma
    if failed_manual:
        print()
        log("Avtomatik ishlamadi — QO'LDA YUKLAB OLING:", "WARN")
        for ds in failed_manual:
            print(f"     🔗 https://images.cv/dataset/{ds['slug']}")
            print(f"        Faqat 'Download' tugmasini bosing (ro'yxat shart emas)")
            print(f"        ZIP -> E:\\sergak_smoking\\datasets\\icv_{ds['name']}\\")

    return total_imgs


# ============================================================
# 🟢 2) SMOKE100K — Akademik smoke detection (sintetik)
# ============================================================
def download_smoke100k():
    header("🟢 2) SMOKE100K — sintetik smoke detection")

    target = DATASETS_DIR / "smoke100k"
    if target.exists() and count_images(target) > 100:
        log(f"Mavjud - {count_images(target):,} rasm", "SKIP")
        return count_images(target)

    log("Smoke100k Google Drive orqali tarqatiladi", "WARN")
    log("Qo'lda yuklab olish kerak:", "INFO")
    print()
    print("    🔗 https://bigmms.github.io/cheng_gcce19_smoke100k/")
    print()
    print("    Saytda Google Drive yoki Baidu linkini toping va yuklab oling")
    print(f"    Keyin: E:\\sergak_smoking\\datasets\\smoke100k\\ ga extract qiling")

    return 0


# ============================================================
# 🟢 3) GITHUB RELEASE FAYLLARI
# ============================================================
GITHUB_RELEASES = [
    {
        "name": "deepquest_fire_smoke",
        "url": "https://github.com/DeepQuestAI/Fire-Smoke-Dataset/releases/download/v1.0/FIRE-SMOKE-DATASET.zip",
        "desc": "DeepQuest Fire+Smoke Dataset"
    },
    {
        "name": "dfs_fire_smoke",
        "url": "https://github.com/siyuanwu/DFS-FIRE-SMOKE-Dataset/releases/download/v1.0.0/DFS-FIRE-SMOKE-Dataset.zip",
        "desc": "DFS Fire+Smoke (siyuanwu)"
    },
]


def download_github_releases():
    header("🟢 3) GitHub RELEASE fayllari")

    if not ensure_package("requests"):
        return 0

    total_imgs = 0
    for i, rel in enumerate(GITHUB_RELEASES, 1):
        target = DATASETS_DIR / f"ghr_{rel['name']}"
        zip_path = DATASETS_DIR / f"ghr_{rel['name']}.zip"
        print()
        print(f"  [{i}/{len(GITHUB_RELEASES)}] {rel['name']}")
        print(f"        {rel['desc']}")

        if target.exists() and count_images(target) > 100:
            log(f"Mavjud - {count_images(target):,} rasm", "SKIP")
            total_imgs += count_images(target)
            continue

        if download_url_to_file(rel["url"], zip_path, rel["name"]):
            if extract_archive(zip_path, target):
                zip_path.unlink()
                imgs = count_images(target)
                if imgs > 0:
                    log(f"OK - {imgs:,} rasm", "OK")
                    total_imgs += imgs
                else:
                    log("Yuklab olindi, rasm yo'q", "WARN")
            else:
                log("Extract xato", "ERR")

    return total_imgs


# ============================================================
# 🟢 4) OPEN IMAGES V7 — FiftyOne (Cigarette klassi)
# ============================================================
def download_open_images_v7():
    header("🏆 4) OPEN IMAGES V7 (Google) — Cigarette klassi")

    target = DATASETS_DIR / "oiv7_cigarette"
    if target.exists() and count_images(target) > 100:
        log(f"Mavjud - {count_images(target):,} rasm", "SKIP")
        return count_images(target)

    log("FiftyOne library o'rnatilmoqda...", "INFO")
    if not ensure_package("fiftyone"):
        log("FiftyOne o'rnatilmadi - skip", "ERR")
        return 0

    try:
        import fiftyone.zoo as foz

        log("Open Images V7'dan 'Cigarette' klassi yuklab olinmoqda...", "DOWN")
        log("Bu 10-30 daqiqa olishi mumkin", "INFO")

        target.mkdir(parents=True, exist_ok=True)

        dataset = foz.load_zoo_dataset(
            "open-images-v7",
            split="train",
            label_types=["detections"],
            classes=["Cigarette"],
            max_samples=5000,
            dataset_dir=str(target),
            shuffle=True,
        )

        imgs = count_images(target)
        log(f"OK - {imgs:,} rasm yuklab olindi", "OK")
        return imgs
    except Exception as e:
        log(f"Xato: {str(e)[:150]}", "ERR")
        return 0


# ============================================================
# MAIN
# ============================================================
def main():
    print()
    print("=" * 72)
    print("  🚀 SERGAK AI - YANGI SIGARET DATASETLAR")
    print("=" * 72)
    print(f"  Manzil: {DATASETS_DIR}")
    print()
    print("  Yangi manbalar:")
    print("    1. images.cv             - 3 ta dataset (~10,300 rasm)")
    print("    2. Smoke100k             - 100K rasm (qo'lda)")
    print("    3. GitHub Releases       - 2 ta dataset")
    print("    4. Open Images V7        - 5,000 cigarette rasm")
    print()

    start_time = time.time()

    icv_imgs = download_images_cv()
    smk_imgs = download_smoke100k()
    ghr_imgs = download_github_releases()
    oiv7_imgs = download_open_images_v7()

    elapsed = time.time() - start_time

    # YAKUNIY HISOBOT
    header("📊 YAKUNIY HISOBOT")

    new_imgs = icv_imgs + smk_imgs + ghr_imgs + oiv7_imgs

    # Eski sanash
    old_imgs = 0
    for d in DATASETS_DIR.iterdir():
        if d.is_dir() and not d.name.startswith(("icv_", "smoke100k", "ghr_", "oiv7_")):
            old_imgs += count_images(d)

    total = new_imgs + old_imgs
    total_size = sum(f.stat().st_size for f in DATASETS_DIR.rglob("*") if f.is_file())

    print(f"  🟢 images.cv:           {icv_imgs:>7,} rasm (YANGI)")
    print(f"  🟢 Smoke100k:           {smk_imgs:>7,} rasm")
    print(f"  🟢 GitHub Releases:     {ghr_imgs:>7,} rasm")
    print(f"  🏆 Open Images V7:      {oiv7_imgs:>7,} rasm")
    print(f"  ──────────────────────────────")
    print(f"  📊 YANGI:               {new_imgs:>7,} rasm")
    print(f"  📊 ESKI:                {old_imgs:>7,} rasm")
    print(f"  📊 JAMI:                {total:>7,} rasm")
    print(f"  💾 Disk:                {total_size/1e9:.2f} GB")
    print(f"  ⏱️  Vaqt:                {elapsed/60:.1f} daqiqa")
    print()

    print("  📁 Barcha datasetlar:")
    grand_total = 0
    for d in sorted(DATASETS_DIR.iterdir()):
        if d.is_dir():
            n = count_images(d)
            if n > 0:
                size_mb = sum(f.stat().st_size for f in d.rglob("*") if f.is_file()) / 1e6
                grand_total += n
                marker = "🟢" if n > 1000 else "🟡" if n > 100 else "⚪"
                print(f"    {marker} {d.name:<45s}  {n:>7,} rasm   {size_mb:>7.1f} MB")

    print()
    print(f"  🎯 GRAND TOTAL: {grand_total:,} rasm")
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
