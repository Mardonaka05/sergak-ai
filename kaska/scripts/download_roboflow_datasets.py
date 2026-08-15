"""
Roboflow datasetlarini avtomatik yuklab oluvchi skript.

ISHLATISH:
    1. Roboflow Private API Key'ni quyidagi qatorga joylang:
         PRIVATE_API_KEY = "rf_xxxxxxxxxxxxxxxxx"

    2. Skriptni ishga tushiring:
         python download_roboflow_datasets.py

    3. Hamma datasetlar avtomatik yuklab olinadi va
       D:\\sergak dasturi\\kaska\\datasets\\ ga joylashadi

XAVFSIZLIK:
    - Bu faylda turgan Private API Key ni hech kim bilan ulashmang
    - Git'ga kommit qilmang
    - Tugagandan keyin kalitni o'chirib qo'ying (xohlasangiz)
"""
import os
import sys
from pathlib import Path

# =============================================================
#  SIZNING PRIVATE API KEY NI BU YERGA JOYLANG (chatga emas!)
#  Roboflow: https://app.roboflow.com/settings/api
# =============================================================
PRIVATE_API_KEY = "FKDfvXn5w6CGC4khaxPF"
# =============================================================

# Datasetlar ro'yxati - barchasi public va helmet detectionga oid
DATASETS = [
    # 1. Joseph Nelson - Hard Hat Workers (eng mashhur)
    {
        "workspace": "joseph-nelson",
        "project": "hard-hat-workers",
        "version": 2,
        "format": "yolov8",
        "out_dir": "roboflow_joseph_hardhat",
    },
    # 2. PPE datasets from Roboflow Universe
    {
        "workspace": "personal-protective-equipment",
        "project": "ppes-kaxsi",
        "version": 4,
        "format": "yolov8",
        "out_dir": "roboflow_ppe",
    },
    # 3. Construction Safety
    {
        "workspace": "object-detection",
        "project": "construction-site-safety",
        "version": 27,
        "format": "yolov8",
        "out_dir": "roboflow_construction_safety",
    },
    # 4. Hard Hat Universe
    {
        "workspace": "test-kanon",
        "project": "hard-hat-yolov8",
        "version": 1,
        "format": "yolov8",
        "out_dir": "roboflow_hardhat_universe",
    },
    # 5. Helmet Detection
    {
        "workspace": "helmet-detection-1elxe",
        "project": "helmet-detection-9d3la",
        "version": 1,
        "format": "yolov8",
        "out_dir": "roboflow_helmet_v2",
    },
]

DATASETS_ROOT = Path(r"D:\sergak dasturi\kaska\datasets")


def check_setup():
    if PRIVATE_API_KEY == "BU_YERGA_SIZNING_PRIVATE_KALITINGIZ":
        print("[X] XATO: Private API Key kiritilmagan!")
        print()
        print("Iltimos quyidagi qadamlarni bajaring:")
        print("  1. https://app.roboflow.com/settings/api ga kiring")
        print("  2. 'Private API Key' ostidagi qulflangan qatorni bosing")
        print("  3. Ko'rinib qolgan kalitni nusxa qiling (rf_... bilan boshlanadi)")
        print("  4. Bu fayldagi PRIVATE_API_KEY = '...' qatoriga joylang")
        print("  5. Faylni saqlab, skriptni qaytadan ishga tushiring")
        sys.exit(1)

    # Roboflow paket o'rnatilganligini tekshirish
    try:
        import roboflow  # noqa
    except ImportError:
        print("[!] roboflow paketi o'rnatilmagan")
        print("    O'rnatish:")
        print(r'      & "D:\sergak dasturi\backend\venv\Scripts\python.exe" -m pip install roboflow')
        sys.exit(1)


def main():
    check_setup()

    from roboflow import Roboflow
    rf = Roboflow(api_key=PRIVATE_API_KEY)

    DATASETS_ROOT.mkdir(parents=True, exist_ok=True)

    print("=" * 64)
    print(f"  Roboflow datasetlarini yuklab olish ({len(DATASETS)} ta)")
    print(f"  Joylashish: {DATASETS_ROOT}")
    print("=" * 64)

    success = 0
    failed = []
    for i, ds in enumerate(DATASETS, 1):
        print(f"\n[{i}/{len(DATASETS)}] {ds['workspace']}/{ds['project']} v{ds['version']}")
        out_path = DATASETS_ROOT / ds["out_dir"]
        if out_path.exists() and list(out_path.glob("**/*.txt")):
            print(f"  [skip] allaqachon mavjud: {out_path}")
            success += 1
            continue
        try:
            # Roboflow SDK ishchi katalogga yuklaydi, keyin uni ko'chiramiz
            orig_cwd = os.getcwd()
            out_path.mkdir(parents=True, exist_ok=True)
            os.chdir(str(out_path))
            try:
                workspace = rf.workspace(ds["workspace"])
                project = workspace.project(ds["project"])
                version = project.version(ds["version"])
                dataset = version.download(ds["format"])
                print(f"  [OK] yuklab olindi: {dataset.location}")
                success += 1
            finally:
                os.chdir(orig_cwd)
        except Exception as e:
            print(f"  [X] xato: {e}")
            failed.append((ds["project"], str(e)))
            continue

    print("\n" + "=" * 64)
    print(f"  Yakuniy: {success}/{len(DATASETS)} ta dataset yuklab olindi")
    if failed:
        print("\n  Muvaffaqiyatsiz datasetlar:")
        for name, err in failed:
            print(f"    [-] {name}: {err[:80]}")
    print("=" * 64)
    print()
    print("  Keyingi qadam:")
    print(r'    python "D:\sergak dasturi\kaska\scripts\merge_datasets.py"')


if __name__ == "__main__":
    main()
