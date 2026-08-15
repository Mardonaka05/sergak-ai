"""
SERGAK AI - SIGARET ANIQLASH LOYIHASI v5.0
============================================
IDEAL RETRY SKRIPT — xato bo'lganlarni qaytadan yuklab olish

Yangiliklar v5.0:
  - 10+ Kaggle datasetlari (eng yaxshilari)
  - Roboflow uchun smart retry (max 2 urinish, tezda fail)
  - Bo'sh papkalarni avtomatik tozalash
  - Already-downloaded skip (100+ rasm bo'lsa)
  - 0 rasmli "false success" larni qayta yuklash
"""
import os
import sys
import shutil
import subprocess
import time
from pathlib import Path

# ============================================================
# KONFIGURATSIYA
# ============================================================
PROJECT_ROOT = Path(r"E:\sergak_smoking")
DATASETS_DIR = PROJECT_ROOT / "datasets"

# Tokenlar
ROBOFLOW_API_KEY = os.environ.get("ROBOFLOW_API_KEY", "FKDfvXn5w6CGC4khaxPF")
KAGGLE_TOKEN = os.environ.get("KAGGLE_API_TOKEN", "KGAT_7f6d388560bec29c6ac64aeb06cc09e5")

# Tezda fail bo'lish - vaqt yo'qotmaslik
ROBOFLOW_MAX_RETRIES = 2     # 2 marta urinib ko'rib qoldirish
ROBOFLOW_TIMEOUT = 60        # 60 sekund (juda uzoq emas)

if not Path("E:\\").exists():
    PROJECT_ROOT = Path(r"D:\sergak dasturi\smoking")
    DATASETS_DIR = PROJECT_ROOT / "datasets"

DATASETS_DIR.mkdir(parents=True, exist_ok=True)


def log(msg, lvl="INFO"):
    symbols = {"INFO": "[i]", "OK": "[+]", "WARN": "[!]", "ERR": "[X]",
               "SKIP": "[-]", "DONE": "[V]", "RETRY": "[R]"}
    print(f"  {symbols.get(lvl, '[?]')} {msg}")


def header(title):
    print()
    print("=" * 72)
    print(f"  {title}")
    print("=" * 72)


def ensure_package(package, import_name=None, upgrade=False):
    import_name = import_name or package
    try:
        if not upgrade:
            __import__(import_name)
            return True
    except ImportError:
        pass
    try:
        cmd = [sys.executable, "-m", "pip", "install", package, "-q", "--disable-pip-version-check"]
        if upgrade:
            cmd.append("--upgrade")
        subprocess.check_call(cmd, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def count_images(directory):
    if not directory.exists():
        return 0
    return sum(1 for f in directory.rglob("*")
               if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp", ".webp"))


def get_size_mb(directory):
    if not directory.exists():
        return 0
    return sum(f.stat().st_size for f in directory.rglob("*") if f.is_file()) / 1e6


def cleanup_bad_datasets():
    """Bo'sh va xato bo'lgan datasetlarni o'chirish."""
    if not DATASETS_DIR.exists():
        return 0
    cleaned = 0
    for d in sorted(DATASETS_DIR.iterdir()):
        if not d.is_dir():
            continue
        try:
            imgs = count_images(d)
            size_mb = get_size_mb(d)
            # Faqat 0 rasm va 5 MB dan kam bo'lsa - bo'sh deb hisoblanadi
            if imgs == 0 and size_mb < 5:
                shutil.rmtree(d)
                cleaned += 1
                log(f"Tozalandi (bo'sh): {d.name}", "SKIP")
        except Exception:
            pass
    return cleaned


# ============================================================
# 🟢 HUGGING FACE
# ============================================================
HF_DATASETS = [
    {"name": "smoke_kerem",  "repo": "keremberke/smoke-object-detection"},
]


def download_huggingface_all():
    header("🟢 HUGGING FACE")

    if not ensure_package("huggingface_hub"):
        return 0, 0

    from huggingface_hub import snapshot_download

    success = 0
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
            success += 1
        except Exception as e:
            log(f"Xato: {str(e)[:120]}", "ERR")

    return success, total_images


# ============================================================
# 🟢 KAGGLE - 10 ta dataset (ko'proq variantlar)
# ============================================================
KAGGLE_DATASETS = [
    # === Tasdiqlangan ishchilar ===
    "prajjwalkumarpanzade/smoking-and-drinking-dataset-for-yolo",  # 1,030 ✅
    "muhammetzahitaydn/cigarette-smoker-dataset",                   # 9,004 ✅
    # === ToS qabul qilingan bo'lsa ishlaydi ===
    "sujaykapadnis/smoker-detection-image-dataset",
    "imbikramsaha/cigarette-detection",
    # === Yangi qo'shilganlar ===
    "vitaminc/cigarette-detection-dataset",
    "iranjith/cigarette-smoking-detection-dataset",
    "ramishbeyzadeh/smoker-detection",
    "harshilpatel355/smoking-dataset",
    "harshilpatel355/cigarette-detection-dataset",
    "kutaykutlu/smoke-detection",
]


def download_kaggle_all():
    header("🟢 KAGGLE - 10 ta dataset")

    # Token tekshirish
    access_token_file = Path.home() / ".kaggle" / "access_token"
    kaggle_json = Path.home() / ".kaggle" / "kaggle.json"

    if not (access_token_file.exists() or kaggle_json.exists() or KAGGLE_TOKEN):
        log("Kaggle token topilmadi!", "ERR")
        log("Token oling: https://www.kaggle.com/settings/account", "INFO")
        return 0, 0

    # Yangi token formatini saqlash (agar yo'q bo'lsa)
    if KAGGLE_TOKEN and not access_token_file.exists():
        access_token_file.parent.mkdir(parents=True, exist_ok=True)
        access_token_file.write_text(KAGGLE_TOKEN)
        log(f"Token saqlandi: {access_token_file}", "OK")

    # Kaggle library yangilash
    ensure_package("kaggle", upgrade=True)

    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        api = KaggleApi()
        api.authenticate()
        log("Kaggle API ulandi", "OK")
    except Exception as e:
        log(f"Auth xato: {e}", "ERR")
        return 0, 0

    success = 0
    failed_tos = []
    failed_other = []
    total_images = 0

    for i, ds_id in enumerate(KAGGLE_DATASETS, 1):
        name = ds_id.split("/")[-1].replace("-", "_")
        target = DATASETS_DIR / f"kgl_{name}"
        print()
        print(f"  [{i:2d}/{len(KAGGLE_DATASETS)}] {ds_id}")

        # Mavjudligini tekshirish
        if target.exists():
            existing = count_images(target)
            if existing > 100:
                log(f"Mavjud - {existing:,} rasm", "SKIP")
                total_images += existing
                continue
            else:
                # Bo'sh - o'chirib qaytadan yuklash
                try:
                    shutil.rmtree(target)
                except Exception:
                    pass

        try:
            target.mkdir(parents=True, exist_ok=True)
            api.dataset_download_files(ds_id, path=str(target), unzip=True, quiet=False)
            imgs = count_images(target)
            if imgs > 0:
                total_images += imgs
                log(f"OK - {imgs:,} rasm", "OK")
                success += 1
            else:
                log(f"Yuklab olindi lekin 0 rasm (CSV/sensor data?)", "WARN")
                try:
                    shutil.rmtree(target)
                except Exception:
                    pass
        except Exception as e:
            err_str = str(e)[:200]
            if "403" in err_str or "Forbidden" in err_str:
                log(f"403 — ToS qabul qilish kerak (link pastda)", "ERR")
                failed_tos.append(ds_id)
            elif "404" in err_str or "not found" in err_str.lower():
                log(f"404 — dataset olib tashlangan", "ERR")
            else:
                log(f"Xato: {err_str[:120]}", "ERR")
                failed_other.append(ds_id)
            try:
                if target.exists() and count_images(target) == 0:
                    shutil.rmtree(target)
            except Exception:
                pass

    # ToS qabul qilinishi kerak bo'lgan datasetlar
    if failed_tos:
        print()
        log("ToS qabul qilish kerak (brauzerda 1 marta ochib 'Accept' bosing):", "INFO")
        for ds in failed_tos:
            print(f"     🔗 https://www.kaggle.com/datasets/{ds}")
        print()
        log("Keyin bu skriptni qayta ishga tushiring", "INFO")

    return success, total_images


# ============================================================
# 🟢 ROBOFLOW - tezda fail bo'lish
# ============================================================
ROBOFLOW_DATASETS = [
    {"name": "smoker_yolo",      "ws": "cigaretteple-7m0hn",     "proj": "smoker-yolo"},
    {"name": "cigarette_h2p1m",  "ws": "yolo-pdvpx",             "proj": "cigarette-h2p1m"},
    {"name": "fire_smoke_human", "ws": "spyrobot",               "proj": "fire-smoke-and-human-detector"},
    {"name": "cig_vape",         "ws": "takoyati",               "proj": "cigarette-vape-detection"},
    {"name": "cig_y1xgi",        "ws": "nehal-lsski",            "proj": "cigarette-detection-y1xgi-szmbd"},
]


def download_roboflow_quick():
    """Roboflow — tezda fail bo'lish, vaqt yo'qotmaslik."""
    header("🟢 ROBOFLOW (tezkor sinov — har biriga 1 urinish)")

    if not ensure_package("roboflow"):
        return 0, 0

    from roboflow import Roboflow
    try:
        rf = Roboflow(api_key=ROBOFLOW_API_KEY)
        log("Roboflow API ulandi", "OK")
    except Exception as e:
        log(f"Ulanish xato: {e}", "ERR")
        return 0, 0

    success = 0
    total_images = 0

    for i, ds in enumerate(ROBOFLOW_DATASETS, 1):
        target = DATASETS_DIR / f"rbf_{ds['name']}"
        print()
        print(f"  [{i}/{len(ROBOFLOW_DATASETS)}] {ds['name']}")

        if target.exists():
            existing = count_images(target)
            if existing > 100:
                log(f"Mavjud - {existing:,} rasm", "SKIP")
                total_images += existing
                continue
            else:
                try:
                    shutil.rmtree(target)
                except Exception:
                    pass

        # Faqat versiya 1 ni sinaymiz - tezda fail bo'lish uchun
        target.mkdir(parents=True, exist_ok=True)
        ok = False
        for ver in [1, 2, 3]:
            try:
                project = rf.workspace(ds["ws"]).project(ds["proj"])
                version = project.version(ver)
                version.download("yolov8", location=str(target))
                imgs = count_images(target)
                if imgs > 0:
                    log(f"v{ver} OK - {imgs:,} rasm", "OK")
                    success += 1
                    total_images += imgs
                    ok = True
                    break
            except Exception as e:
                if "not found" in str(e).lower():
                    continue
                # Network xato - keyingisini sinab ko'rmaymiz
                break

        if not ok:
            log("Network/CDN muammosi - qo'lda yuklab oling", "WARN")
            try:
                if target.exists() and count_images(target) == 0:
                    shutil.rmtree(target)
            except Exception:
                pass

    return success, total_images


# ============================================================
# 📋 Roboflow QO'LDA YUKLAB OLISH KO'RSATMASI
# ============================================================
def print_roboflow_manual():
    print()
    print("=" * 72)
    print("  📋 ROBOFLOW — QO'LDA YUKLAB OLISH")
    print("=" * 72)
    print()
    print("  TOP 5 dataset (eng zo'r — qo'lda yuklab oling):")
    print()
    print("  ┌──┬───────────────────────────┬──────────┬──────────────────────────────────────────┐")
    print("  │ #│ Dataset                   │ Rasmlar  │ Link                                      │")
    print("  ├──┼───────────────────────────┼──────────┼──────────────────────────────────────────┤")
    print("  │ 1│ Cigarette Det (nehal)     │ 8,666 ⭐│ universe.roboflow.com/nehal-lsski/        │")
    print("  │ 2│ Fire Smoke Human          │ 9,749 ⭐│ universe.roboflow.com/spyrobot/           │")
    print("  │ 3│ Cigarette VAPE            │ 5,774 ⭐│ universe.roboflow.com/takoyati/           │")
    print("  │ 4│ Cigarette ghnlk           │ 4,900   │ universe.roboflow.com/cigarette-c6554/    │")
    print("  │ 5│ Smoker YOLO               │ 4,127   │ universe.roboflow.com/cigaretteple-7m0hn/ │")
    print("  └──┴───────────────────────────┴──────────┴──────────────────────────────────────────┘")
    print()
    print("  LINKLAR (brauzerda ochib 'Download Dataset' bosing -> YOLOv8 format):")
    print()
    print("    1. https://universe.roboflow.com/nehal-lsski/cigarette-detection-y1xgi-szmbd")
    print("    2. https://universe.roboflow.com/spyrobot/fire-smoke-and-human-detector")
    print("    3. https://universe.roboflow.com/takoyati/cigarette-vape-detection")
    print("    4. https://universe.roboflow.com/cigarette-c6554/cigarette-ghnlk")
    print("    5. https://universe.roboflow.com/cigaretteple-7m0hn/smoker-yolo")
    print()
    print("  ZIPNI: E:\\sergak_smoking\\datasets\\rbf_<nom>\\ ga extract qiling")


# ============================================================
# MAIN
# ============================================================
def main():
    print()
    print("=" * 72)
    print("  SERGAK AI - SIGARET DATASETLAR v5.0 (IDEAL RETRY)")
    print("=" * 72)
    print(f"  Manzil:    {DATASETS_DIR}")
    print(f"  Reja:      Roboflow (tezkor) + HF + Kaggle (10 ta)")
    print()

    # Avval bo'sh papkalarni tozalash
    log("Bo'sh papkalarni tozalash...", "INFO")
    cleaned = cleanup_bad_datasets()
    if cleaned:
        log(f"{cleaned} ta bo'sh papka tozalandi", "OK")

    start_time = time.time()

    # Yuklab olish tartibi: HF (oson) -> Kaggle (yaxshi) -> Roboflow (qiyin)
    hf_count, hf_imgs = download_huggingface_all()
    kgl_count, kgl_imgs = download_kaggle_all()
    rbf_count, rbf_imgs = download_roboflow_quick()

    elapsed = time.time() - start_time

    # ===== YAKUNIY HISOBOT =====
    header("YAKUNIY HISOBOT")

    total_imgs = rbf_imgs + hf_imgs + kgl_imgs
    total_size = sum(f.stat().st_size for f in DATASETS_DIR.rglob("*") if f.is_file())

    print(f"  📦 Roboflow:        {rbf_count:>3} dataset, {rbf_imgs:>7,} rasm")
    print(f"  📦 HuggingFace:     {hf_count:>3} dataset, {hf_imgs:>7,} rasm")
    print(f"  📦 Kaggle:          {kgl_count:>3} dataset, {kgl_imgs:>7,} rasm")
    print(f"  ─────────────────────────────────────")
    print(f"  📊 JAMI:            {rbf_count+hf_count+kgl_count:>3} dataset, {total_imgs:>7,} rasm")
    print(f"  💾 Disk hajmi:      {total_size/1e9:.2f} GB")
    print(f"  ⏱️  Vaqt:            {elapsed/60:.1f} daqiqa")
    print()

    print(f"  📁 Joylashish: {DATASETS_DIR}")
    print()
    print("  Yuklab olingan datasetlar:")
    for d in sorted(DATASETS_DIR.iterdir()):
        if d.is_dir():
            n = count_images(d)
            if n > 0:
                size_mb = get_size_mb(d)
                print(f"    ✅ {d.name:<45s}  {n:>7,} rasm   {size_mb:>7.1f} MB")
    print()

    # Roboflow qo'lda yo'l-yo'riq (agar kam bo'lsa)
    if rbf_imgs < 5000:
        print_roboflow_manual()

    # Training tayyorligi
    print()
    print("=" * 72)
    print("  TRAINING TAYYORLIGI")
    print("=" * 72)
    if total_imgs >= 30000:
        print(f"  ✅ {total_imgs:,} rasm — MUKAMMAL! Training boshlash mumkin.")
    elif total_imgs >= 20000:
        print(f"  ✅ {total_imgs:,} rasm — YAXSHI. Training boshlash mumkin.")
    elif total_imgs >= 10000:
        print(f"  🟡 {total_imgs:,} rasm — Boshlash mumkin, lekin ko'proq tavsiya etiladi.")
    else:
        print(f"  ⚠️  Faqat {total_imgs:,} rasm. Roboflow'ni qo'lda yuklab oling.")
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
