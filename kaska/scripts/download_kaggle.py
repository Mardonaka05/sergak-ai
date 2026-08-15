"""
Kaggle'dan helmet detection datasetlarini yuklash.

Yangi Kaggle API token formati (KGAT_...) bilan ishlaydi.
Token quyidagi joylardan o'qiladi (tartib bo'yicha):
  1. KAGGLE_API_TOKEN environment variable
  2. C:\\Users\\<user>\\.kaggle\\access_token (yangi format - faqat token)
  3. C:\\Users\\<user>\\.kaggle\\kaggle.json (eski format - JSON)
"""
import os
import sys
from pathlib import Path

DATASETS_ROOT = Path(r"D:\sergak dasturi\kaska\datasets")

KAGGLE_DATASETS = [
    {
        "name": "kaggle_hardhat_andrewmvd",
        "id": "andrewmvd/hard-hat-detection",
        "desc": "Hard Hat Detection (5000 rasm, VOC)",
    },
    {
        "name": "kaggle_yolo_helmethead",
        "id": "vodan37/yolo-helmethead",
        "desc": "YOLO Helmet Head (5000+ rasm, YOLO)",
    },
    {
        "name": "kaggle_construction_safety",
        "id": "snehilsanyal/construction-site-safety-image-dataset-roboflow",
        "desc": "Construction Site Safety (2800 rasm, YOLO)",
    },
    {
        "name": "kaggle_shwd_mirror",
        "id": "whenamancodes/helmet-detection-yolov5",
        "desc": "SHWD mirror (7500+ rasm)",
    },
    {
        "name": "kaggle_ppe_detection",
        "id": "snehilsanyal/personal-protective-equipment-detection",
        "desc": "PPE Detection (7000 rasm)",
    },
]


def ensure_token():
    """Token mavjudligini tekshirish - har xil joylarda izlash."""
    # 1. Env variable
    token = os.environ.get("KAGGLE_API_TOKEN")
    if token:
        print(f"[+] Token topildi: KAGGLE_API_TOKEN env var")
        return True

    # 2. access_token file (yangi format)
    home = Path.home()
    token_file = home / ".kaggle" / "access_token"
    if token_file.exists():
        token = token_file.read_text().strip()
        if token:
            os.environ["KAGGLE_API_TOKEN"] = token
            print(f"[+] Token topildi: {token_file}")
            return True

    # 3. kaggle.json (eski format)
    json_file = home / ".kaggle" / "kaggle.json"
    if json_file.exists():
        print(f"[+] Token topildi (eski format): {json_file}")
        return True

    print("[X] Kaggle token topilmadi!")
    print()
    print("  Setup uchun 1d_setup_kaggle_and_download.bat ni ishga tushiring")
    return False


def main():
    if not ensure_token():
        sys.exit(1)

    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except ImportError:
        print("[!] kaggle paketi yo'q")
        print(r'    & "D:\sergak dasturi\backend\venv\Scripts\python.exe" -m pip install kaggle')
        sys.exit(1)

    api = KaggleApi()
    try:
        api.authenticate()
        print("[+] Kaggle bilan ulandi")
    except Exception as e:
        print(f"[X] Authentication xato: {e}")
        sys.exit(1)

    DATASETS_ROOT.mkdir(parents=True, exist_ok=True)

    print()
    print("=" * 70)
    print(f"  Kaggle'dan {len(KAGGLE_DATASETS)} ta dataset yuklash")
    print("=" * 70)

    success = 0
    failed_list = []
    total_new = 0
    for i, ds in enumerate(KAGGLE_DATASETS, 1):
        print(f"\n[{i}/{len(KAGGLE_DATASETS)}] {ds['name']}")
        print(f"  {ds['desc']}")
        print(f"  ID: {ds['id']}")

        target = DATASETS_ROOT / ds['name']
        if target.exists() and any(target.rglob("*.txt") if target.exists() else []):
            n = sum(1 for f in target.rglob("*")
                    if f.suffix.lower() in (".jpg", ".jpeg", ".png"))
            if n > 50:
                print(f"  [skip] allaqachon mavjud ({n} ta rasm)")
                success += 1
                total_new += n
                continue

        target.mkdir(parents=True, exist_ok=True)
        try:
            print(f"  Yuklanmoqda...")
            api.dataset_download_files(
                ds['id'], path=str(target), unzip=True, quiet=False
            )
            n_imgs = sum(1 for f in target.rglob("*")
                         if f.suffix.lower() in (".jpg", ".jpeg", ".png"))
            print(f"  [OK] {n_imgs} ta rasm yuklandi")
            success += 1
            total_new += n_imgs
        except Exception as e:
            err_str = str(e)[:200]
            print(f"  [X] xato: {err_str}")
            failed_list.append((ds['id'], err_str))

    print()
    print("=" * 70)
    print(f"  YAKUN: {success}/{len(KAGGLE_DATASETS)} muvaffaqiyatli")
    print(f"  Jami rasmlar (yangi): ~{total_new}")
    print("=" * 70)

    if failed_list:
        print()
        print("  Muvaffaqiyatsizlar:")
        for did, err in failed_list:
            print(f"    [-] {did}: {err[:80]}")


if __name__ == "__main__":
    main()
