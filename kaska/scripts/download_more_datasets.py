"""
QO'SHIMCHA datasetlarni yuklab olish — Roboflow Universe'dan ko'p variant sinash.

Strategiya: 15+ ta nomzod datasetni sinab ko'rish. Har bittasi ishlamasligi mumkin,
lekin 5-8 tasi muvaffaqiyatli yuklanishi va 10,000+ yangi rasm qo'shilishi kerak.
"""
import os
import sys
import time
from pathlib import Path

# =============================================================
#  Private API Key — allaqachon qo'yilgan
# =============================================================
PRIVATE_API_KEY = "FKDfvXn5w6CGC4khaxPF"
# =============================================================

# Yangi nomzod datasetlar (Roboflow Universe'dan)
# Format: (workspace, project, version, output_folder_name)
CANDIDATE_DATASETS = [
    # === Hard hat / helmet detection ===
    ("hard-hat-detection-pmkv9", "hard-hat-detection", 1, "rf_hardhat_pmkv9"),
    ("helmet-detection-9d3la", "helmet-detection-1elxe", 1, "rf_helmet_9d3la"),
    ("workspace-d9bxg", "helmet-detection-2-cs26h", 1, "rf_helmet_d9bxg"),
    ("hardhatpalin", "hard-hat-w7p2g", 1, "rf_hardhat_palin"),
    ("school-frjam", "helmet-detection-bqvqg", 1, "rf_helmet_school"),
    ("smart-yard", "helmet-detection-pdrvg", 1, "rf_helmet_yard"),
    ("project-2-uuxat", "helmet-only-r1lho", 1, "rf_helmet_only"),
    ("helmetdataset", "helmetdataset-evfqu", 1, "rf_helmetdataset"),
    ("ppe-detection-eqczg", "helmet-detection-eqfwq", 1, "rf_ppe_eqczg"),
    ("hardhats", "hardhats", 1, "rf_hardhats"),

    # === Construction safety / PPE ===
    ("roboflow-100", "construction-safety", 1, "rf100_construction"),
    ("constructionsite", "construction-safety-detection", 1, "rf_construction_site"),
    ("safetyhelmet", "helmet-z1mph", 1, "rf_safetyhelmet"),
    ("safety-helmet", "helmet-detection-u4wjj", 1, "rf_safety_helmet"),
    ("hard-hat-rdvxl", "hard-hat-detection-rdvxl", 1, "rf_hardhat_rdvxl"),
]

DATASETS_ROOT = Path(r"D:\sergak dasturi\kaska\datasets")


def main():
    try:
        from roboflow import Roboflow
    except ImportError:
        print("[!] roboflow paketi yo'q — o'rnatish:")
        print('    & "D:\\sergak dasturi\\backend\\venv\\Scripts\\python.exe" -m pip install roboflow')
        sys.exit(1)

    rf = Roboflow(api_key=PRIVATE_API_KEY)
    DATASETS_ROOT.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print(f"  QO'SHIMCHA datasetlarni yuklab olish ({len(CANDIDATE_DATASETS)} ta nomzod)")
    print("=" * 70)
    print("\n  Eslatma: ba'zilari ishlamasligi mumkin — bu normal.")
    print("  Maqsadimiz: 5-10 ta yangi datasetni muvaffaqiyatli yuklash.\n")

    success = 0
    failed = 0
    failed_list = []
    total_new_images = 0

    for i, (workspace, project, version, out_name) in enumerate(CANDIDATE_DATASETS, 1):
        print(f"\n[{i}/{len(CANDIDATE_DATASETS)}] {workspace}/{project} v{version}")
        out_path = DATASETS_ROOT / out_name
        if out_path.exists() and list(out_path.glob("**/*.txt")):
            print(f"  [skip] allaqachon mavjud: {out_name}")
            success += 1
            continue
        try:
            orig_cwd = os.getcwd()
            out_path.mkdir(parents=True, exist_ok=True)
            os.chdir(str(out_path))
            try:
                ws = rf.workspace(workspace)
                proj = ws.project(project)
                ver = proj.version(version)
                dataset = ver.download("yolov8")

                # Yuklab olingan rasmlarni sanash
                n_images = 0
                for img_dir in out_path.glob("**/images"):
                    n_images += sum(1 for f in img_dir.glob("*")
                                    if f.suffix.lower() in (".jpg", ".jpeg", ".png"))
                print(f"  [OK] {n_images} ta rasm")
                success += 1
                total_new_images += n_images
            finally:
                os.chdir(orig_cwd)
        except Exception as e:
            print(f"  [X] xato: {str(e)[:80]}")
            failed += 1
            failed_list.append(f"{workspace}/{project}")
            # Bo'sh papkani tozalash
            try:
                if out_path.exists() and not list(out_path.iterdir()):
                    out_path.rmdir()
            except Exception:
                pass
        # Kichik pauza (Roboflow API rate limit)
        time.sleep(1)

    print("\n" + "=" * 70)
    print(f"  YAKUN: {success} muvaffaqiyatli, {failed} muvaffaqiyatsiz")
    print(f"  Yangi rasmlar: ~{total_new_images}")
    print("=" * 70)

    if failed_list:
        print("\n  Muvaffaqiyatsizlar (workspace yoki versiya noto'g'ri):")
        for f in failed_list[:10]:
            print(f"    - {f}")
        if len(failed_list) > 10:
            print(f"    ... va yana {len(failed_list)-10}")

    print("\n  KEYINGI QADAM:")
    print("    Yangi datasetlarni hisobga olib qaytadan birlashtirish:")
    print(r'    cd "D:\sergak dasturi\kaska"')
    print(r'    .\2_merge_datasets.bat')
    print()


if __name__ == "__main__":
    main()
