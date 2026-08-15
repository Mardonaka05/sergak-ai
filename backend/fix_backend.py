"""
Sergak AI - BACKEND FIX SKRIPTI (SMART)
=========================================
Bu skript HAR BIR modul uchun ENG ANIQ (mAP eng yuqori) .pt faylini topadi.

Tartib:
  1. Modulning hamma mos kelishi mumkin bo'lgan .pt fayllarini topadi
  2. Har birini tahlil qiladi (mAP@0.5, klasslar, arxitektura)
  3. ENG YUQORI mAP'lisini tanlaydi
  4. DB'ga saqlaydi

Talab:
  - Backend DB tayyor (sergak.db yoki MySQL)
  - PyTorch o'rnatilgan (tahlil uchun)

Ishlatish:
  python fix_backend.py
  python fix_backend.py --dry-run
"""
import argparse
import asyncio
import fnmatch
import json
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))


# ============ Modul → fayl shablonlari ============
# Birinchi mos kelganidan boshlab, hammasi tahlil qilinadi va eng yaxshisi tanlanadi.

MODULE_FILE_PATTERNS = {
    "helmet": ["sergak_helmet*.pt", "helmet*.pt", "kaska*.pt"],
    "smoking": ["smoking*.pt", "sigaret*.pt", "cigarette*.pt"],
    "fire": ["fire*.pt", "flame*.pt", "yongin*.pt"],
    "phone": ["phone*.pt", "mobile*.pt", "telefon*.pt"],
    "fall": ["fall*.pt", "yiqilish*.pt"],
    "smoke": ["smoke*.pt", "tutun*.pt", "fume*.pt"],
    "mask": ["mask*.pt", "niqob*.pt"],
    "vest": ["vest*.pt", "jilet*.pt", "reflective*.pt"],
    "glove": ["glove*.pt", "qol*.pt"],
}


def log(msg, level="INFO"):
    symbols = {"INFO": "[i]", "OK": "[+]", "WARN": "[!]", "ERR": "[X]",
               "SKIP": "[-]", "DRY": "[~]", "BEST": "[*]"}
    print(f"  {symbols.get(level, '[?]')} {msg}")


def header(title):
    print()
    print("=" * 76)
    print(f"  {title}")
    print("=" * 76)


# ============ .pt fayllarni topish ============

def find_all_pt_files():
    """Find all .pt files in models/ and models_pt/."""
    files = {}
    for subdir in ["models", "models_pt"]:
        d = BASE / subdir
        if not d.exists():
            continue
        for pt in d.glob("*.pt"):
            files[pt.name] = {
                "path": pt,
                "size_mb": round(pt.stat().st_size / (1024 * 1024), 1),
                "subdir": subdir,
                "mtime": datetime.fromtimestamp(pt.stat().st_mtime),
            }
    return files


def candidates_for_module(key, all_files):
    """Modul uchun mos kelishi mumkin bo'lgan barcha .pt fayllarini topish."""
    patterns = MODULE_FILE_PATTERNS.get(key, [f"{key}*.pt"])
    found = []
    seen_names = set()
    for pat in patterns:
        for fname, info in all_files.items():
            if fname in seen_names:
                continue
            if fnmatch.fnmatch(fname.lower(), pat.lower()):
                found.append(info)
                seen_names.add(fname)
    return found


# ============ .pt faylni tahlil qilish ============

def inspect_pt(pt_path):
    """Tahlil natijasi: {map50, num_classes, names, arch, has_class_match}"""
    info = {
        "map50": 0.0,           # mAP@0.5 (foiz)
        "map50_95": 0.0,        # mAP@0.5:0.95
        "precision": 0.0,
        "recall": 0.0,
        "num_classes": 0,
        "class_names": [],
        "architecture": "",
        "epoch": 0,
        "valid": True,
        "in_filename_mAP": 0.0,  # masalan "_94mAP" → 94.0
    }

    # Fayl nomidan mAP olish (masalan "sergak_helmet_v1_94mAP.pt" → 94)
    import re
    m = re.search(r'(\d+(?:\.\d+)?)\s*mAP', pt_path.name, re.IGNORECASE)
    if m:
        try:
            info["in_filename_mAP"] = float(m.group(1))
        except Exception:
            pass

    try:
        import torch
        ckpt = torch.load(str(pt_path), map_location="cpu", weights_only=False)

        info["epoch"] = ckpt.get("epoch", 0) or 0

        # Class names
        names = ckpt.get("names")
        model_obj = ckpt.get("model")
        if not names and model_obj is not None:
            names = getattr(model_obj, "names", None)
        if names:
            if isinstance(names, dict):
                info["class_names"] = [str(names[i]) for i in sorted(names.keys())]
            elif isinstance(names, list):
                info["class_names"] = [str(n) for n in names]
            info["num_classes"] = len(info["class_names"])

        # Metrics from training
        bm = ckpt.get("best_metrics") or ckpt.get("train_metrics") or {}
        for k, v in (bm.items() if isinstance(bm, dict) else []):
            try:
                v = float(v)
            except Exception:
                continue
            kl = str(k).lower()
            if "map50-95" in kl or "map_0.5:0.95" in kl:
                info["map50_95"] = v * 100 if v < 1.5 else v
            elif "map50" in kl or "map(0.5)" in kl:
                info["map50"] = v * 100 if v < 1.5 else v
            elif "precision" in kl:
                info["precision"] = v * 100 if v < 1.5 else v
            elif "recall" in kl:
                info["recall"] = v * 100 if v < 1.5 else v

        # Filename mAP majburiy mAP'dan kuchli (chunki ko'pincha
        # production .pt da metrics tozalangan bo'ladi)
        if info["in_filename_mAP"] > info["map50"]:
            info["map50"] = info["in_filename_mAP"]

        # Architecture from size
        size_mb = pt_path.stat().st_size / (1024 * 1024)
        if size_mb < 8: info["architecture"] = "YOLOv8n"
        elif size_mb < 25: info["architecture"] = "YOLOv8s"
        elif size_mb < 60: info["architecture"] = "YOLOv8m"
        elif size_mb < 100: info["architecture"] = "YOLOv8l"
        else: info["architecture"] = "YOLOv8l-full"
    except ImportError:
        info["valid"] = False
    except Exception as e:
        info["valid"] = False
        log(f"Tahlil xato {pt_path.name}: {e}", "ERR")
    return info


def score_for_module(module_key, info, pt_info):
    """Modul uchun .pt fayl ballini hisoblash. Ko'p ball = yaxshiroq.

    Faktorlar:
      1. Klass nomi modul kalitiga mos kelsa (helmet, smoking, etc.) +30
      2. mAP@0.5 yuqori +0..100
      3. Stripped (87 MB YOLOv8l) production-ready +10
      4. Yangi sana (recent) +0..5
    """
    score = 0.0

    # 1) Klass mos kelishi (eng muhim)
    classes_lower = " ".join(info.get("class_names", [])).lower()
    if module_key in classes_lower:
        score += 30

    # Module → kutilgan klasslar
    expected_classes = {
        "helmet": ["helmet", "hard_hat", "hardhat", "kaska", "head"],
        "smoking": ["smoking", "smoker", "cigarette"],
        "fire": ["fire", "flame"],
        "smoke": ["smoke"],
        "phone": ["phone", "mobile", "cell_phone"],
        "fall": ["fall", "fallen", "person_fall"],
        "mask": ["mask", "face_mask"],
        "vest": ["vest", "reflective_vest"],
        "glove": ["glove"],
    }
    for cls in expected_classes.get(module_key, []):
        if cls in classes_lower:
            score += 5
            break

    # 2) mAP — eng katta vazn
    score += info["map50"]  # 0..100

    # 3) Production-ready (stripped 60-100 MB YOLOv8l)
    if 60 < pt_info["size_mb"] < 100:
        score += 10
    elif pt_info["size_mb"] > 300:
        score -= 5  # full state — kattaroq, lekin ishlatish uchun ortiqcha

    # 4) Yangi fayl (oxirgi 60 kun ichida)
    days_old = (datetime.now() - pt_info["mtime"]).days
    if days_old < 30:
        score += 5
    elif days_old < 60:
        score += 3

    return score


# ============ Asosiy fix logikasi ============

async def fix_modules(dry_run=False):
    from app.core.database import AsyncSessionLocal, init_db
    from app.models.module import Module
    from sqlalchemy import select

    header("1) BARCHA .PT FAYLLARNI TOPISH")
    all_files = find_all_pt_files()
    if not all_files:
        log("Hech qanday .pt fayl topilmadi", "ERR")
        return False

    for name, info in sorted(all_files.items(), key=lambda x: -x[1]["size_mb"]):
        log(f"{name:<45s} {info['size_mb']:>7} MB   ({info['subdir']})", "OK")

    header("2) DB MODULLARINI O'QISH")
    async with AsyncSessionLocal() as db:
        modules = (await db.execute(select(Module).order_by(Module.id))).scalars().all()
        log(f"DB'da {len(modules)} ta modul", "OK")

        header("3) HAR BIR MODUL UCHUN ENG YAXSHI .PT'NI TANLASH")
        fixed = 0

        for m in modules:
            print()
            log(f"━━ Modul: '{m.key}' ({m.name}) ━━", "INFO")

            candidates = candidates_for_module(m.key, all_files)
            if not candidates:
                log("Mos .pt fayl yo'q — o'tkazib yuborildi", "WARN")
                continue

            # Hammasini tahlil qilish va ball berish
            scored = []
            for cand in candidates:
                info = inspect_pt(cand["path"])
                if not info["valid"]:
                    log(f"   {cand['path'].name:<35s} → noma'lum (skip)", "SKIP")
                    continue
                score = score_for_module(m.key, info, cand)
                scored.append({
                    "info": info,
                    "file": cand,
                    "score": score,
                })
                mAP_str = f"{info['map50']:.1f}%" if info['map50'] > 0 else "?"
                classes_str = ", ".join(info.get("class_names", [])[:3])
                log(f"   {cand['path'].name:<40s}  mAP={mAP_str:>6}  score={score:>6.1f}  klasslar=[{classes_str}]", "INFO")

            if not scored:
                continue

            # Eng yuqori ball
            scored.sort(key=lambda s: -s["score"])
            best = scored[0]

            log(f"GOLIB: {best['file']['path'].name}", "BEST")
            log(f"   mAP@0.5:        {best['info']['map50']:.2f}%", "BEST")
            log(f"   Arxitektura:    {best['info']['architecture']}", "BEST")
            log(f"   Klasslar:       {best['info']['class_names']}", "BEST")

            # DB'ni yangilash
            new_path = str(best["file"]["path"].resolve())
            if m.model_path == new_path and m.class_names not in ("[]", "", None):
                log("Allaqachon to'g'ri — o'zgarmadi", "SKIP")
                continue

            if dry_run:
                log("(--dry-run — saqlanmadi)", "DRY")
                continue

            m.model_path = new_path
            m.model_filename = best["file"]["path"].name
            m.file_size_mb = best["file"]["size_mb"]
            m.architecture = best["info"]["architecture"]
            m.class_names = json.dumps(best["info"]["class_names"], ensure_ascii=False)
            m.num_classes = best["info"]["num_classes"]
            if best["info"]["map50"] > 0:
                m.accuracy_pct = round(best["info"]["map50"], 2)
            m.updated_at = datetime.utcnow()
            fixed += 1

        if not dry_run and fixed > 0:
            await db.commit()
            log(f"\n{fixed} ta modul yangilandi", "OK")
        elif fixed == 0:
            log("\nO'zgarishsiz — hammasi to'g'ri", "OK")

    return True


async def print_summary():
    from app.core.database import AsyncSessionLocal
    from app.models.module import Module
    from sqlalchemy import select

    header("4) YAKUNIY HOLAT")
    async with AsyncSessionLocal() as db:
        modules = (await db.execute(select(Module).order_by(Module.id))).scalars().all()
        print(f"  {'#':<3} {'Key':<10} {'mAP':>7} {'Arxitektura':<14} {'Fayl':<35} {'Status'}")
        print("  " + "-" * 100)
        for m in modules:
            try:
                names = json.loads(m.class_names or "[]")
            except Exception:
                names = []
            status = "READY" if m.model_path and Path(m.model_path).exists() else "NO FILE"
            mAP = f"{m.accuracy_pct:.1f}%" if m.accuracy_pct else "-"
            fname = (m.model_filename or "-")[:35]
            print(f"  {m.id:<3} {m.key:<10} {mAP:>7} {m.architecture:<14} {fname:<35} {status}")


# ============ Main ============

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print()
    print("=" * 76)
    print("  SERGAK AI - SMART BACKEND FIX (eng aniq .pt avtomatik tanlash)")
    print("=" * 76)
    print(f"  Bosh papka:  {BASE}")
    print(f"  Rejim:       {'DRY-RUN' if args.dry_run else 'TUZATISH'}")

    try:
        from app.core.database import init_db
        await init_db()
        log("DB tayyor", "OK")
    except Exception as e:
        log(f"DB xato: {e}", "ERR")
        log("MySQL ishlamasa, .env'da SQLite'ga o'tkazing", "WARN")
        return

    ok = await fix_modules(dry_run=args.dry_run)
    if not ok:
        return

    await print_summary()

    header("TAYYOR!")
    if args.dry_run:
        print("  DRY-RUN. Saqlash uchun: python fix_backend.py")
    else:
        print("  Tuzatildi. Backend ni qayta ishga tushiring:")
        print("    python -m app.main")
    print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[!] To'xtatildi")
    except Exception as e:
        print(f"\n[X] XATO: {e}")
        import traceback
        traceback.print_exc()
