"""
SERGAK AI - IDEAL DATASET TEKSHIRUVI (HTML HISOBOT BILAN)
==========================================================
Har bir dataset uchun:
  1. Klasslarni aniqlash (folder/yaml/filename)
  2. Klass bo'yicha rasm sonini sanash
  3. 10 ta NAMUNA rasm ko'chirish
  4. HTML hisobot yaratish (brauzerda thumbnailar bilan)
  5. Verdict (smoking?/skip?)

Natija: E:\\sergak_smoking\\inspection_report.html
"""
from pathlib import Path
from collections import Counter, defaultdict
import shutil
import re
import random
import base64
import html

# YANGI joylashuv (extract qilingach)
DATASETS_DIR = Path(r"D:\sergak dasturi\sergak_smoking\datasets")
SAMPLES_DIR = Path(r"D:\sergak dasturi\sergak_smoking\samples")
REPORT_HTML = Path(r"D:\sergak dasturi\sergak_smoking\inspection_report.html")

# Agar yangi yo'l yo'q bo'lsa - eski E:\ ga qaytish
if not DATASETS_DIR.exists():
    DATASETS_DIR = Path(r"E:\sergak_smoking\datasets")
    SAMPLES_DIR = Path(r"E:\sergak_smoking\samples")
    REPORT_HTML = Path(r"E:\sergak_smoking\inspection_report.html")

random.seed(42)
SAMPLES_PER_CLASS = 8  # har klassdan 8 ta namuna


def log(msg, lvl="INFO"):
    symbols = {"INFO": "[i]", "OK": "[+]", "WARN": "[!]", "ERR": "[X]"}
    print(f"  {symbols.get(lvl, '[?]')} {msg}")


# ============================================================
# KLASS ANIQLASH
# ============================================================
SMOKING_KEYWORDS = ["smoking", "smoker", "cigarette", "cigarettes", "cig",
                    "cigarrette", "tobacco", "vape"]
NO_SMOKING_KEYWORDS = ["not_smoking", "non_smoking", "notsmoking", "non-smoking",
                       "no_smoking", "non_smoker", "no_smoker", "normal", "drinking"]


def classify_by_folder(name):
    n = name.lower().strip().replace("-", "_").replace(" ", "_")
    for kw in NO_SMOKING_KEYWORDS:
        if kw in n.split("_") or kw == n:
            return "no_smoking"
    if any(kw in n for kw in NO_SMOKING_KEYWORDS):
        return "no_smoking"
    for kw in SMOKING_KEYWORDS:
        if kw == n or kw in n.split("_"):
            return "smoking"
    if any(kw in n for kw in SMOKING_KEYWORDS):
        return "smoking"
    return None


def classify_by_filename(filename):
    n = filename.lower()
    if n.startswith(("notsmoking", "not_smoking", "non_smoking", "nonsmoking", "no_")):
        return "no_smoking"
    if n.startswith(("smoking", "smoker", "cigarette", "cig_", "tobacco")):
        return "smoking"
    if re.match(r"^(abc|aa|aagg|ii)\d+", n):
        return "smoking"  # mnd datasetlarning konventsiyasi
    return None


# ============================================================
# DATASET TAHLILI
# ============================================================
def analyze_dataset(d):
    """Bitta datasetni to'liq tahlil qilish."""
    info = {
        "name": d.name,
        "format": "unknown",
        "yaml_classes": [],
        "yaml_bbox_counts": Counter(),
        "folder_classes": defaultdict(list),  # smoking: [img1, img2], no_smoking: [...]
        "filename_classes": defaultdict(list),
        "total_images": 0,
        "verdict": "?",
        "comment": "",
        "samples_per_class": {},
    }

    # 1. Hamma rasmlarni topish (cache va boshqalarni skip qilish)
    all_imgs = []
    for f in d.rglob("*"):
        try:
            if not f.is_file():
                continue
            # .cache, .git papkalarini skip
            if any(p in (".cache", ".git", "__pycache__") for p in f.parts):
                continue
            if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp"):
                all_imgs.append(f)
        except Exception:
            continue
    info["total_images"] = len(all_imgs)

    # 2. data.yaml ni tekshirish
    yamls = list(d.rglob("data.yaml"))
    if yamls:
        info["format"] = "YOLO"
        try:
            text = yamls[0].read_text(encoding="utf-8", errors="ignore")
            m = re.search(r"names\s*:\s*\[([^\]]+)\]", text)
            if m:
                info["yaml_classes"] = [n.strip().strip("'\"") for n in m.group(1).split(",")]
            else:
                m = re.search(r"names\s*:\s*\n((?:\s*-\s*[^\n]+\n?)+)", text)
                if m:
                    info["yaml_classes"] = [l.strip().lstrip("-").strip().strip("'\"")
                                             for l in m.group(1).split("\n") if l.strip()]
                else:
                    pairs = re.findall(r"^\s*(\d+)\s*:\s*['\"]?([^'\"\n]+?)['\"]?\s*$",
                                        text, re.MULTILINE)
                    if pairs:
                        info["yaml_classes"] = [p[1].strip() for p in
                                                 sorted(pairs, key=lambda x: int(x[0]))]
        except Exception:
            pass

        # Bbox sanash
        if info["yaml_classes"]:
            txts = [f for f in d.rglob("*.txt")
                    if f.name not in ("README.txt", "classes.txt", "requirements.txt")]
            for txt in txts[:5000]:
                try:
                    for line in txt.read_text().strip().split("\n"):
                        parts = line.split()
                        if len(parts) >= 5:
                            try:
                                cls = int(parts[0])
                                if 0 <= cls < len(info["yaml_classes"]):
                                    info["yaml_bbox_counts"][info["yaml_classes"][cls]] += 1
                            except ValueError:
                                pass
                except Exception:
                    continue

    # 3. Folder strukturasini tekshirish (smoking/not_smoking folders)
    for img in all_imgs:
        # Path'dagi har bir papka nomini tekshirish
        for parent in img.parents:
            if parent == d or parent == d.parent:
                break
            cls = classify_by_folder(parent.name)
            if cls:
                info["folder_classes"][cls].append(img)
                break

    # 4. Filename asosida klassifikatsiya
    for img in all_imgs:
        cls = classify_by_filename(img.name)
        if cls:
            info["filename_classes"][cls].append(img)

    # 5. Format aniqlash
    if info["format"] == "unknown":
        if info["folder_classes"]:
            info["format"] = "FOLDERS"
        elif info["filename_classes"]:
            info["format"] = "FILENAMES"
        elif all_imgs:
            info["format"] = "RAW IMAGES"

    # 6. Verdict
    info["verdict"], info["comment"] = make_verdict(info)

    # 7. Namuna rasmlarni tanlash
    if info["yaml_classes"]:
        # YOLO format - umumiy sample
        info["samples_per_class"]["yolo_all"] = random.sample(
            all_imgs, min(SAMPLES_PER_CLASS, len(all_imgs))
        ) if all_imgs else []
    if info["folder_classes"]:
        for cls, imgs in info["folder_classes"].items():
            info["samples_per_class"][f"folder_{cls}"] = random.sample(
                imgs, min(SAMPLES_PER_CLASS, len(imgs))
            )
    if info["filename_classes"]:
        for cls, imgs in info["filename_classes"].items():
            info["samples_per_class"][f"filename_{cls}"] = random.sample(
                imgs, min(SAMPLES_PER_CLASS, len(imgs))
            )
    if not info["samples_per_class"] and all_imgs:
        info["samples_per_class"]["all"] = random.sample(
            all_imgs, min(SAMPLES_PER_CLASS, len(all_imgs))
        )

    return info


def make_verdict(info):
    """Verdict qaror."""
    name = info["name"].lower()
    cls = [c.lower() for c in info["yaml_classes"]]

    # Smoke/fire (sigaret emas)
    if "smoke" in name and "smoking" not in name and "smoker" not in name:
        return "SKIP", "Smoke/fire detection (sigaret emas)"
    if "fire" in name and "cigarette" not in name:
        return "SKIP", "Fire detection (sigaret emas)"
    if "indoor_smoke" in name or "fire_smoke" in name:
        return "SKIP", "Yong'in/tutun (sigaret emas)"

    # YOLO classes contain smoke/fire but NOT smoking
    if cls and all((c in ["fire", "smoke", "flame", "default", "0", "1"]) for c in cls):
        if not any("smoking" in c or "cigarette" in c or "smoker" in c for c in cls):
            return "SKIP", f"Faqat: {cls} (sigaret emas)"

    # Has smoking/cigarette class
    if any("smoking" in c or "cigarette" in c or "smoker" in c for c in cls):
        return "USE", f"YOLO smoking klassi: {cls}"

    # Folder-based smoking
    if "smoking" in info["folder_classes"] or "no_smoking" in info["folder_classes"]:
        sm = len(info["folder_classes"].get("smoking", []))
        nm = len(info["folder_classes"].get("no_smoking", []))
        return "USE", f"Folder: smoking={sm}, no_smoking={nm}"

    # Filename-based smoking
    if "smoking" in info["filename_classes"] or "no_smoking" in info["filename_classes"]:
        sm = len(info["filename_classes"].get("smoking", []))
        nm = len(info["filename_classes"].get("no_smoking", []))
        return "USE", f"Filename: smoking={sm}, no_smoking={nm}"

    # Too few images
    if info["total_images"] < 20:
        return "SKIP", f"Juda kam ({info['total_images']} rasm)"

    # Name has smoking/cigarette
    if any(kw in name for kw in ["smoking", "smoker", "cigarette", "cig"]):
        return "CHECK", "Sigaret nomi bor, namunalarni ko'ring"

    return "UNKNOWN", "Qo'lda tekshirish"


# ============================================================
# HTML HISOBOT
# ============================================================
def encode_image_base64(img_path, max_size=(200, 200)):
    """Rasmni base64 ga aylantirib HTML ga embedding qilish (kichraytirib)."""
    try:
        from PIL import Image
        img = Image.open(img_path)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.thumbnail(max_size)
        import io
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=70)
        b64 = base64.b64encode(buf.getvalue()).decode()
        return f"data:image/jpeg;base64,{b64}"
    except Exception:
        return ""


def generate_html_report(all_results):
    """HTML hisobot yaratish."""
    log("HTML hisobot yaratilmoqda...", "INFO")

    # Stats
    use_count = sum(1 for r in all_results if r["verdict"] == "USE")
    skip_count = sum(1 for r in all_results if r["verdict"] == "SKIP")
    check_count = sum(1 for r in all_results if r["verdict"] == "CHECK")
    unknown_count = sum(1 for r in all_results if r["verdict"] == "UNKNOWN")

    total_use_imgs = sum(r["total_images"] for r in all_results if r["verdict"] == "USE")

    html_parts = ['''<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<title>Sergak AI - Sigaret Datasetlar Inspectiyasi</title>
<style>
body { font-family: -apple-system, Segoe UI, sans-serif; background: #1a1a2e; color: #e0e0e0; padding: 20px; max-width: 1400px; margin: 0 auto; }
h1 { color: #ffd700; border-bottom: 3px solid #ffd700; padding-bottom: 10px; }
.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0; }
.stat { background: #16213e; padding: 20px; border-radius: 10px; text-align: center; border-left: 5px solid #4caf50; }
.stat.use { border-color: #4caf50; }
.stat.skip { border-color: #f44336; }
.stat.check { border-color: #ff9800; }
.stat.unknown { border-color: #9e9e9e; }
.stat h2 { margin: 0; font-size: 2.5em; }
.stat p { margin: 5px 0 0; opacity: 0.8; }
.dataset { background: #16213e; margin: 20px 0; padding: 20px; border-radius: 10px; border-left: 5px solid #555; }
.dataset.use { border-color: #4caf50; }
.dataset.skip { border-color: #f44336; opacity: 0.7; }
.dataset.check { border-color: #ff9800; }
.dataset.unknown { border-color: #9e9e9e; }
.dataset h3 { margin-top: 0; color: #ffd700; }
.verdict { display: inline-block; padding: 5px 15px; border-radius: 20px; font-weight: bold; margin-left: 15px; }
.verdict.use { background: #4caf50; }
.verdict.skip { background: #f44336; }
.verdict.check { background: #ff9800; }
.verdict.unknown { background: #9e9e9e; }
.info-grid { display: grid; grid-template-columns: 200px 1fr; gap: 10px; margin: 15px 0; }
.info-grid b { color: #ffd700; }
.classes { background: #0f3460; padding: 10px; border-radius: 5px; margin: 10px 0; }
.samples { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px; margin-top: 15px; }
.sample { background: #0f3460; padding: 8px; border-radius: 5px; text-align: center; }
.sample img { max-width: 180px; max-height: 180px; border-radius: 3px; }
.sample p { margin: 5px 0 0; font-size: 0.85em; color: #aaa; word-wrap: break-word; }
.section-title { color: #ffd700; margin-top: 20px; border-bottom: 1px solid #555; padding-bottom: 5px; }
</style>
</head>
<body>
<h1>🚬 Sergak AI - Sigaret Datasetlar Inspectiyasi</h1>
''']

    html_parts.append(f'''
<div class="stats">
  <div class="stat use"><h2>{use_count}</h2><p>🟢 USE</p></div>
  <div class="stat check"><h2>{check_count}</h2><p>🟡 CHECK</p></div>
  <div class="stat skip"><h2>{skip_count}</h2><p>🔴 SKIP</p></div>
  <div class="stat"><h2>{total_use_imgs:,}</h2><p>📊 USE Rasmlar</p></div>
</div>
''')

    # Datasetlarni tartiblash: USE birinchi, CHECK ikkinchi, SKIP oxiriga
    order = {"USE": 0, "CHECK": 1, "UNKNOWN": 2, "SKIP": 3}
    sorted_results = sorted(all_results, key=lambda r: (order.get(r["verdict"], 9), r["name"]))

    for info in sorted_results:
        verdict_class = info["verdict"].lower()
        html_parts.append(f'''
<div class="dataset {verdict_class}">
  <h3>📁 {html.escape(info["name"])}
    <span class="verdict {verdict_class}">{info["verdict"]}</span>
  </h3>
  <div class="info-grid">
    <b>Format:</b> <span>{info["format"]}</span>
    <b>Rasmlar:</b> <span>{info["total_images"]:,}</span>
    <b>Comment:</b> <span>{html.escape(info["comment"])}</span>
  </div>
''')

        # YOLO klasslari
        if info["yaml_classes"]:
            html_parts.append('<div class="classes"><b>YAML Klasslar:</b><ul>')
            for c in info["yaml_classes"]:
                bbox = info["yaml_bbox_counts"].get(c, 0)
                html_parts.append(f'<li>{html.escape(c)} — {bbox:,} bbox</li>')
            html_parts.append('</ul></div>')

        # Folder klasslari
        if info["folder_classes"]:
            html_parts.append('<div class="classes"><b>Folder Klasslar:</b><ul>')
            for c, imgs in info["folder_classes"].items():
                html_parts.append(f'<li>{html.escape(c)} — {len(imgs):,} rasm</li>')
            html_parts.append('</ul></div>')

        # Filename klasslari
        if info["filename_classes"]:
            html_parts.append('<div class="classes"><b>Filename Klasslar:</b><ul>')
            for c, imgs in info["filename_classes"].items():
                html_parts.append(f'<li>{html.escape(c)} — {len(imgs):,} rasm</li>')
            html_parts.append('</ul></div>')

        # Namuna rasmlar
        for section, samples in info["samples_per_class"].items():
            if not samples:
                continue
            html_parts.append(f'<h4 class="section-title">🖼️ {html.escape(section)}</h4>')
            html_parts.append('<div class="samples">')
            for img in samples:
                b64 = encode_image_base64(img)
                if b64:
                    html_parts.append(
                        f'<div class="sample"><img src="{b64}" /><p>{html.escape(img.name[:30])}</p></div>'
                    )
            html_parts.append('</div>')

        html_parts.append('</div>')

    html_parts.append('</body></html>')

    REPORT_HTML.parent.mkdir(parents=True, exist_ok=True)
    REPORT_HTML.write_text("".join(html_parts), encoding="utf-8")
    log(f"HTML saqlandi: {REPORT_HTML}", "OK")


# ============================================================
# MAIN
# ============================================================
def main():
    print()
    print("=" * 80)
    print("  SERGAK AI - IDEAL DATASET TEKSHIRUVI")
    print("=" * 80)
    print(f"  Kirish:    {DATASETS_DIR}")
    print(f"  Namunalar: {SAMPLES_DIR}")
    print(f"  Hisobot:   {REPORT_HTML}")
    print()

    if not DATASETS_DIR.exists():
        print(f"[X] Topilmadi: {DATASETS_DIR}")
        return

    # Pillow tekshirish
    try:
        from PIL import Image
    except ImportError:
        import subprocess
        log("Pillow o'rnatilmoqda...", "INFO")
        subprocess.check_call(["python", "-m", "pip", "install", "Pillow", "-q"])

    # Avvalgi samples'ni tozalash
    if SAMPLES_DIR.exists():
        try:
            shutil.rmtree(SAMPLES_DIR)
        except Exception:
            pass

    all_results = []
    for d in sorted(DATASETS_DIR.iterdir()):
        if not d.is_dir():
            continue
        log(f"Tahlil: {d.name}", "INFO")
        try:
            info = analyze_dataset(d)
            all_results.append(info)
        except Exception as e:
            log(f"Xato {d.name}: {e}", "ERR")
            continue

    # KONSOLE HISOBOTI
    print()
    print("=" * 80)
    print("  KONSOL HISOBOTI")
    print("=" * 80)

    use_list = [r for r in all_results if r["verdict"] == "USE"]
    check_list = [r for r in all_results if r["verdict"] == "CHECK"]
    skip_list = [r for r in all_results if r["verdict"] == "SKIP"]
    unknown_list = [r for r in all_results if r["verdict"] == "UNKNOWN"]

    use_total = sum(r["total_images"] for r in use_list)
    check_total = sum(r["total_images"] for r in check_list)
    skip_total = sum(r["total_images"] for r in skip_list)

    print(f"\n  USE ({len(use_list)}) — {use_total:,} rasm:")
    for r in use_list:
        sm = sum(len(v) for k, v in r["folder_classes"].items() if "smoking" == k) + \
             sum(len(v) for k, v in r["filename_classes"].items() if "smoking" == k) + \
             sum(b for c, b in r["yaml_bbox_counts"].items() if "smok" in c.lower() or "cig" in c.lower())
        nm = sum(len(v) for k, v in r["folder_classes"].items() if "no_smoking" == k) + \
             sum(len(v) for k, v in r["filename_classes"].items() if "no_smoking" == k)
        print(f"    USE  {r['name']:<48s}  total={r['total_images']:>6,}  smoking={sm:>5,}  no_smoking={nm:>5,}")

    print(f"\n  CHECK ({len(check_list)}) — {check_total:,} rasm:")
    for r in check_list:
        print(f"    CHK  {r['name']:<48s}  total={r['total_images']:>6,}  ({r['comment']})")

    print(f"\n  SKIP ({len(skip_list)}) — {skip_total:,} rasm:")
    for r in skip_list:
        print(f"    SKP  {r['name']:<48s}  total={r['total_images']:>6,}  ({r['comment']})")

    if unknown_list:
        print(f"\n  UNKNOWN ({len(unknown_list)}):")
        for r in unknown_list:
            print(f"    UNK  {r['name']:<48s}  total={r['total_images']:>6,}")

    print()
    print("=" * 80)
    print(f"  YAKUN:")
    print(f"    SMOKING (USE):  {use_total:>7,} rasm  ({len(use_list)} dataset)")
    print(f"    SHUBHALI (CHK): {check_total:>7,} rasm  ({len(check_list)} dataset)")
    print(f"    EMAS (SKIP):    {skip_total:>7,} rasm  ({len(skip_list)} dataset)")
    print("=" * 80)

    # HTML HISOBOT
    try:
        generate_html_report(all_results)
    except Exception as e:
        log(f"HTML xato: {e}", "ERR")

    print()
    print("=" * 80)
    print(f"  HTML HISOBOTNI OCHISH:")
    print(f"    explorer \"{REPORT_HTML}\"")
    print("=" * 80)
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
