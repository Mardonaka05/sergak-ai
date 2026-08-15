"""
SERGAK AI - DATASETLARNI CHUQUR TAHLIL QILISH
==============================================
Har bir dataset uchun:
  1. Strukturasini chuqur tekshirish
  2. Klasslarini ko'rsatish (haqiqiy nomlari)
  3. Rasmlar sonini sanash
  4. 5 ta NAMUNA RASMni samples\ ga ko'chirish
  5. Tavsiya berish (smoking? cigarette? smoke? skip?)

Foydalanuvchi keyin samples\ papkasini ochib ko'radi.
"""
from pathlib import Path
from collections import Counter
import shutil
import re
import random

DATASETS_DIR = Path(r"E:\sergak_smoking\datasets")
SAMPLES_DIR = Path(r"E:\sergak_smoking\samples")

if not Path("E:\\").exists():
    DATASETS_DIR = Path(r"D:\sergak dasturi\smoking\datasets")
    SAMPLES_DIR = Path(r"D:\sergak dasturi\smoking\samples")

random.seed(42)


def log(msg, lvl="INFO"):
    symbols = {"INFO": "[i]", "OK": "[+]", "WARN": "[!]", "ERR": "[X]",
               "SKIP": "[-]", "DONE": "[V]"}
    print(f"  {symbols.get(lvl, '[?]')} {msg}")


# ============================================================
# YORDAMCHI FUNKSIYALAR
# ============================================================
def find_data_yaml(d):
    """data.yaml fayllarini topish."""
    return list(d.rglob("data.yaml"))


def parse_yaml_classes(yaml_path):
    """data.yaml dan klasslarni o'qish."""
    try:
        text = yaml_path.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"names\s*:\s*\[([^\]]+)\]", text)
        if m:
            return [n.strip().strip("'\"") for n in m.group(1).split(",")]
        m = re.search(r"names\s*:\s*\n((?:\s*-\s*[^\n]+\n?)+)", text)
        if m:
            return [l.strip().lstrip("-").strip().strip("'\"")
                    for l in m.group(1).split("\n") if l.strip()]
        pairs = re.findall(r"^\s*(\d+)\s*:\s*['\"]?([^'\"\n]+?)['\"]?\s*$", text, re.MULTILINE)
        if pairs:
            return [p[1].strip() for p in sorted(pairs, key=lambda x: int(x[0]))]
    except Exception:
        pass
    return []


def count_bboxes(d, num_classes):
    """Har bir klassning bbox sonini sanash."""
    counter = Counter()
    txts = [f for f in d.rglob("*.txt")
            if f.name not in ("README.txt", "classes.txt", "requirements.txt")]
    for txt in txts:
        try:
            for line in txt.read_text().strip().split("\n"):
                parts = line.split()
                if len(parts) >= 5:
                    try:
                        cls = int(parts[0])
                        if 0 <= cls < num_classes:
                            counter[cls] += 1
                    except ValueError:
                        pass
        except Exception:
            continue
    return counter


def find_folder_structure(d):
    """Folder-asosli strukturalarni topish (smoking/not_smoking)."""
    folder_imgs = {}
    # 1-2 level chuqurlikgacha
    for sub1 in d.iterdir():
        if not sub1.is_dir():
            continue
        # Bevosita rasmlar
        direct_imgs = [f for f in sub1.iterdir()
                       if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp")]
        if direct_imgs:
            folder_imgs[sub1.name] = direct_imgs

        # 2-level (train/test/valid -> smoking/not_smoking)
        for sub2 in sub1.iterdir():
            if not sub2.is_dir():
                continue
            inner_imgs = [f for f in sub2.iterdir()
                          if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp")]
            if inner_imgs:
                key = f"{sub1.name}/{sub2.name}"
                folder_imgs[key] = inner_imgs

    return folder_imgs


def collect_samples(images_list, count=3):
    """Ro'yxatdan tasodifiy 3 ta rasm tanlash."""
    if not images_list:
        return []
    random.seed(42)
    n = min(count, len(images_list))
    return random.sample(images_list, n)


def copy_samples(samples, dst_dir, prefix=""):
    """Namuna rasmlarni ko'chirish."""
    dst_dir.mkdir(parents=True, exist_ok=True)
    copied = []
    for i, img in enumerate(samples):
        try:
            new_name = f"{prefix}_sample_{i+1}{img.suffix}"
            dst = dst_dir / new_name
            shutil.copy2(str(img), str(dst))
            copied.append(dst)
        except Exception:
            pass
    return copied


# ============================================================
# DATASET TAHLILI
# ============================================================
def analyze_dataset(d):
    """Bitta datasetni to'liq tahlil qilish."""
    info = {
        "name": d.name,
        "format": "unknown",
        "classes": [],
        "bbox_counts": {},
        "folder_counts": {},
        "total_images": 0,
        "samples": [],
        "verdict": "unknown",
        "comment": "",
    }

    # 1. data.yaml borligini tekshirish
    yamls = find_data_yaml(d)
    if yamls:
        info["format"] = "YOLO"
        info["classes"] = parse_yaml_classes(yamls[0])

        # Bbox sanash
        if info["classes"]:
            counts = count_bboxes(d, len(info["classes"]))
            info["bbox_counts"] = {info["classes"][i]: counts.get(i, 0)
                                    for i in range(len(info["classes"]))}

    # 2. Folder strukturasini tekshirish
    folders = find_folder_structure(d)
    info["folder_counts"] = {k: len(v) for k, v in folders.items()}

    # 3. Hamma rasmlarni sanash
    all_imgs = [f for f in d.rglob("*")
                if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp")]
    info["total_images"] = len(all_imgs)

    if info["format"] == "unknown" and folders:
        info["format"] = "FOLDERS"

    if info["format"] == "unknown" and all_imgs:
        # YOLO label borligini tekshirish
        txts = [f for f in d.rglob("*.txt")
                if f.name not in ("README.txt", "classes.txt", "requirements.txt")]
        if len(txts) >= 5:
            info["format"] = "YOLO (no yaml)"
        else:
            info["format"] = "RAW IMAGES"

    # 4. Namuna rasmlar
    if folders:
        # Folder asosida — har papkadan 2 ta rasm
        for folder_name, imgs in folders.items():
            samples = collect_samples(imgs, 2)
            for s in samples:
                info["samples"].append((folder_name, s))
    elif all_imgs:
        # Random 5 ta rasm
        samples = collect_samples(all_imgs, 5)
        for s in samples:
            info["samples"].append(("root", s))

    # 5. Verdict (qaror)
    info["verdict"], info["comment"] = make_verdict(info)

    return info


def make_verdict(info):
    """Datasetga qaror chiqarish."""
    name = info["name"].lower()
    classes = [c.lower() for c in info["classes"]] if info["classes"] else []
    folders = [f.lower() for f in info["folder_counts"].keys()]

    # Folder nomlarini ko'rib chiqish
    has_smoking_folder = any("smok" in f or "cig" in f for f in folders if "not" not in f and "non" not in f)
    has_not_smoking_folder = any(("not" in f.split("/")[-1] or "non" in f.split("/")[-1] or "no_" in f.split("/")[-1])
                                  for f in folders)

    # SMOKE/FIRE darrak (sigaret emas)
    smoke_keywords = ["smoke_kerem", "indoor_smoke", "fire_smoke", "smoke_mnusrat", "smoke_abonia"]
    if any(kw in name for kw in smoke_keywords):
        if not any("smoking" in c or "cigarette" in c for c in classes):
            return "🔴 SKIP",  "Smoke/fire detection — sigaretchekuvchi emas"

    # YOLO with cigarette/smoking class
    if classes:
        smoking_classes = [c for c in classes if "smok" in c or "cig" in c]
        if smoking_classes:
            return "🟢 USE", f"YOLO format, smoking klasslari: {smoking_classes}"

    # Folder-based with smoking subfolder
    if has_smoking_folder and has_not_smoking_folder:
        return "🟢 USE", f"Folder-based: smoking/not_smoking — IDEAL"
    elif has_smoking_folder:
        return "🟡 PARTIAL", "Faqat smoking folder — half useful"

    # Multi-class YOLO with smoke
    if classes and any("smoke" in c or "fire" in c for c in classes):
        if not any("smoking" in c or "cig" in c for c in classes):
            return "🔴 SKIP", f"Faqat smoke/fire: {classes}"

    # Cigarette in name
    if "cig" in name or "cigarette" in name:
        return "🟡 CHECK", "Cigarette dataseti — namunalarni ko'ring"

    # Smoking in name
    if "smoking" in name or "smoker" in name:
        return "🟡 CHECK", "Smoking dataseti — namunalarni ko'ring"

    if info["total_images"] < 10:
        return "🔴 SKIP", "Juda kam rasm (faqat kod)"

    return "❓ UNKNOWN", "Qo'lda tekshirish kerak"


# ============================================================
# MAIN
# ============================================================
def main():
    print()
    print("=" * 90)
    print("  🔍 SERGAK AI - DATASETLAR CHUQUR TAHLIL")
    print("=" * 90)
    print(f"  📁 Kirish:    {DATASETS_DIR}")
    print(f"  📁 Namunalar: {SAMPLES_DIR}")
    print()

    if not DATASETS_DIR.exists():
        print(f"[X] Topilmadi: {DATASETS_DIR}")
        return

    # Avvalgi samples'ni tozalash
    if SAMPLES_DIR.exists():
        try:
            shutil.rmtree(SAMPLES_DIR)
        except Exception:
            pass
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

    all_results = []
    for d in sorted(DATASETS_DIR.iterdir()):
        if not d.is_dir():
            continue

        log(f"Tahlil qilinmoqda: {d.name}", "INFO")
        info = analyze_dataset(d)

        # Namunalarni ko'chirish
        if info["samples"]:
            ds_samples_dir = SAMPLES_DIR / d.name
            for i, (folder_name, img_path) in enumerate(info["samples"][:5]):
                try:
                    folder_safe = folder_name.replace("/", "_").replace("\\", "_")
                    new_name = f"{folder_safe}_{i+1}{img_path.suffix}"
                    dst = ds_samples_dir / new_name
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(img_path), str(dst))
                except Exception:
                    pass

        all_results.append(info)

    # =========================
    # HISOBOT — har bir dataset
    # =========================
    for info in all_results:
        print()
        print("┌" + "─" * 88 + "┐")
        print(f"│ 📁 {info['name']:<82s} │")
        print("├" + "─" * 88 + "┤")
        print(f"│ Format:        {info['format']:<71s} │")
        print(f"│ Rasmlar:       {info['total_images']:>7,} ta                                                       │")
        print(f"│ Verdict:       {info['verdict']:<71s} │")
        print(f"│ Comment:       {info['comment'][:70]:<71s} │")

        # Klasslar
        if info['classes']:
            print(f"│ Klasslar:                                                                                │")
            for i, c in enumerate(info['classes']):
                bbox = info['bbox_counts'].get(c, 0)
                print(f"│   [{i}] {c:<30s}  {bbox:>7,} bbox                                       │")

        # Folderlar
        if info['folder_counts']:
            print(f"│ Folderlar (rasm soni bilan):                                                             │")
            for folder, count in sorted(info['folder_counts'].items(), key=lambda x: -x[1])[:8]:
                print(f"│   {folder[:35]:<35s}  {count:>7,} rasm                                       │")

        # Namuna fayllar
        if info['samples']:
            print(f"│ Namuna rasmlar (samples\\{info['name']}\\ ga ko'chirildi):                                 │")
            for folder_name, img in info['samples'][:3]:
                print(f"│   • {folder_name}/{img.name[:50]:<50s}                          │")

        print("└" + "─" * 88 + "┘")

    # =========================
    # YAKUNIY HISOBOT
    # =========================
    print()
    print("=" * 90)
    print("  📊 YAKUNIY HISOBOT")
    print("=" * 90)

    use_datasets = [r for r in all_results if "🟢" in r['verdict']]
    check_datasets = [r for r in all_results if "🟡" in r['verdict']]
    skip_datasets = [r for r in all_results if "🔴" in r['verdict']]
    unknown_datasets = [r for r in all_results if "❓" in r['verdict']]

    print(f"  🟢 USE (to'g'ridan-to'g'ri ishlatamiz):  {len(use_datasets)} dataset")
    for r in use_datasets:
        print(f"     ✅ {r['name']:<45s}  {r['total_images']:>6,} rasm  ({r['comment'][:40]})")

    print()
    print(f"  🟡 CHECK (namunalarni qo'lda ko'ring):  {len(check_datasets)} dataset")
    for r in check_datasets:
        print(f"     🔍 {r['name']:<45s}  {r['total_images']:>6,} rasm  ({r['comment'][:40]})")

    print()
    print(f"  🔴 SKIP (sigaret emas):  {len(skip_datasets)} dataset")
    for r in skip_datasets:
        print(f"     ❌ {r['name']:<45s}  {r['total_images']:>6,} rasm  ({r['comment'][:40]})")

    if unknown_datasets:
        print()
        print(f"  ❓ NOMA'LUM:  {len(unknown_datasets)} dataset")
        for r in unknown_datasets:
            print(f"     ? {r['name']:<45s}  {r['total_images']:>6,} rasm")

    # JAMI
    use_total = sum(r['total_images'] for r in use_datasets)
    check_total = sum(r['total_images'] for r in check_datasets)
    skip_total = sum(r['total_images'] for r in skip_datasets)

    print()
    print("  📈 RAQAMLAR:")
    print(f"     🟢 USE:    {use_total:>7,} rasm")
    print(f"     🟡 CHECK:  {check_total:>7,} rasm")
    print(f"     🔴 SKIP:   {skip_total:>7,} rasm")
    print(f"     ────────────────────────")
    print(f"     📊 JAMI:   {use_total + check_total + skip_total:>7,} rasm")
    print()
    print(f"  🎯 Sergak AI uchun kutilgan: {use_total + check_total:,} rasm")
    print()
    print("=" * 90)
    print("  ⚡ KEYINGI QADAM")
    print("=" * 90)
    print()
    print("  1. Brauzer/Explorer'da samples papkasini oching:")
    print(f"        explorer \"{SAMPLES_DIR}\"")
    print()
    print("  2. Har bir dataset uchun namuna rasmlarni KO'RING:")
    print("     - Smoking person aniq ko'rinmoqdami?")
    print("     - Smoke (tutun) emas, sigaret bormi?")
    print()
    print("  3. Tasdiqlangach: 10_prepare.bat ni ishga tushiring")
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
