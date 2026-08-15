"""
GitHub'dan helmet detection datasetlarini yuklash.
Hech qanday API kalit kerak emas - faqat git kerak.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

DATASETS_ROOT = Path(r"D:\sergak dasturi\kaska\datasets")

# GitHub repolari - hammasi ochiq, login kerak emas
GITHUB_REPOS = [
    {
        "name": "pictor_ppe",
        "url": "https://github.com/ciber-lab/pictor-ppe.git",
        "desc": "Pictor PPE - construction PPE (~1500+ images)",
    },
    {
        "name": "smart_construction",
        "url": "https://github.com/PeterH0323/Smart_Construction.git",
        "desc": "Smart Construction - helmet detection dataset",
    },
    {
        "name": "safety_helmet_yolov8",
        "url": "https://github.com/sanchitvj/Safety-Helmet-Detection-using-YOLOv8.git",
        "desc": "Safety helmet detection with YOLOv8",
    },
]


def has_git():
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def main():
    if not has_git():
        print("[X] git o'rnatilmagan!")
        print()
        print("  Git'ni yuklab oling: https://git-scm.com/download/win")
        print("  O'rnating, keyin bu skriptni qaytadan ishga tushiring.")
        sys.exit(1)

    DATASETS_ROOT.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print(f"  GitHub'dan {len(GITHUB_REPOS)} ta dataset yuklash")
    print("=" * 70)
    print()

    success = 0
    for i, repo in enumerate(GITHUB_REPOS, 1):
        print(f"\n[{i}/{len(GITHUB_REPOS)}] {repo['name']}")
        print(f"  {repo['desc']}")
        target = DATASETS_ROOT / repo['name']
        if target.exists() and any(target.iterdir()):
            print(f"  [skip] allaqachon mavjud")
            success += 1
            continue
        try:
            print(f"  git clone {repo['url']}...")
            result = subprocess.run(
                ["git", "clone", "--depth", "1", repo['url'], str(target)],
                capture_output=True, text=True, timeout=600
            )
            if result.returncode == 0:
                # Rasm va label sanash
                n_imgs = sum(1 for f in target.rglob("*")
                             if f.suffix.lower() in (".jpg", ".jpeg", ".png"))
                n_lbls = sum(1 for f in target.rglob("*.txt"))
                print(f"  [OK] {n_imgs} ta rasm, {n_lbls} ta label fayl")
                success += 1
            else:
                print(f"  [X] xato: {result.stderr[:200]}")
        except subprocess.TimeoutExpired:
            print(f"  [X] timeout (10 daqiqa)")
        except Exception as e:
            print(f"  [X] xato: {e}")

    print()
    print("=" * 70)
    print(f"  YAKUN: {success}/{len(GITHUB_REPOS)} muvaffaqiyatli")
    print("=" * 70)


if __name__ == "__main__":
    main()
