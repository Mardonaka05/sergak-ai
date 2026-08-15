"""
Sergak AI - Avtomatik kamera va modul sozlash skripti

Bu skript bir martada quyidagilarni bajaradi:
1. .pt fayllarni $PT_SOURCE_DIR
   dan backend\\models_pt\\ ga ko'chiradi
2. 4 ta Hikvision kamerani DB ga qo'shadi (NVR orqali, IP .env faylidan olinadi)
3. 5 ta AI modulni mos .pt fayllarga bog'laydi va faollashtiradi
4. Har bir kameraga barcha modullarni biriktiradi

ISHLATISH:
    cd "backend"
    venv\\Scripts\\python.exe setup_cameras_and_modules.py
"""
import asyncio
import os
import json
import shutil
import sys
from pathlib import Path
from datetime import datetime

# ============ SOZLAMALAR ============
# Kamera NVR konfiguratsiyasi
NVR_IP   = os.getenv("NVR_IP", "192.168.1.10")
NVR_USER = os.getenv("NVR_USER", "admin")
NVR_PASS = os.getenv("NVR_PASS", "")
NVR_PORT = int(os.getenv("NVR_PORT", "554"))

# Kameralar ro'yxati (NVR kanal raqamlari)
CAMERAS = [
    {"channel": 1, "name": "Kamera-1 (Pechkaxona kirish)",     "location": "G'arbiy eshik",     "dept_key": "eritish"},
    {"channel": 2, "name": "Kamera-2 (Pechkaxona asosiy)",     "location": "Markaziy zona",     "dept_key": "eritish"},
    {"channel": 3, "name": "Kamera-3 (Pechkaxona shimoliy)",   "location": "Shimoliy burchak",  "dept_key": "eritish"},
    {"channel": 4, "name": "Kamera-4 (Pechkaxona chiqish)",    "location": "Sharqiy chiqish",   "dept_key": "eritish"},
]

# .pt fayllar manbai va modullarga bog'lanishi
PT_SOURCE_DIR = Path(os.getenv("PT_SOURCE_DIR", "./models"))
MODELS_DEST_DIR = Path(__file__).parent / "models_pt"

# Modul kalit -> .pt fayl nom va metadata
MODULE_TO_PT = {
    "helmet":  {"file": "helmet_best.pt",  "version": "v1", "arch": "YOLOv8m"},
    "phone":   {"file": "phone_best.pt",   "version": "v1", "arch": "YOLOv8s"},
    "smoking": {"file": "smoke_best.pt",   "version": "v1", "arch": "YOLOv8m"},
    "fall":    {"file": "fall_best.pt",    "version": "v1", "arch": "YOLOv8s"},
    "fire":    {"file": "fire_best.pt",    "version": "v1", "arch": "YOLOv8l"},
}

# Har kameraga biriktiriladigan modullar
DEFAULT_MODULES_PER_CAMERA = ["helmet", "phone", "smoking", "fall", "fire"]

# =====================================

sys.path.insert(0, str(Path(__file__).resolve().parent))


def step(n, msg):
    print(f"\n[{n}] {msg}")
    print("-" * 60)


async def main():
    print("=" * 64)
    print("  SERGAK AI - Kamera va modul avtomatik sozlash")
    print("=" * 64)
    print(f"  NVR:        rtsp://{NVR_USER}:***@{NVR_IP}:{NVR_PORT}")
    print(f"  Kameralar:  {len(CAMERAS)} ta")
    print(f"  Modullar:   {len(MODULE_TO_PT)} ta (.pt fayllar bilan)")
    print("=" * 64)

    # ====== 1. .pt fayllarni ko'chirish ======
    step(1, ".pt fayllarni models_pt/ ga ko'chirish")
    MODELS_DEST_DIR.mkdir(parents=True, exist_ok=True)
    if not PT_SOURCE_DIR.exists():
        print(f"   [!] Manba topilmadi: {PT_SOURCE_DIR}")
        print(f"   [!] To'g'rilab keyin qayta ishga tushiring.")
        return
    copied = {}
    for mod_key, info in MODULE_TO_PT.items():
        src = PT_SOURCE_DIR / info["file"]
        dst = MODELS_DEST_DIR / info["file"]
        if not src.exists():
            print(f"   [X] {info['file']:25s}  topilmadi: {src}")
            copied[mod_key] = None
            continue
        if dst.exists() and dst.stat().st_size == src.stat().st_size:
            size_mb = round(dst.stat().st_size / (1024 * 1024), 2)
            print(f"   [OK] {info['file']:25s}  allaqachon mavjud ({size_mb} MB)")
            copied[mod_key] = str(dst)
            continue
        print(f"   [...] {info['file']:25s}  ko'chirilmoqda...")
        shutil.copy2(src, dst)
        size_mb = round(dst.stat().st_size / (1024 * 1024), 2)
        print(f"   [OK] {info['file']:25s}  ko'chirildi ({size_mb} MB)")
        copied[mod_key] = str(dst)

    # ====== 2. DB ga ulanish ======
    step(2, "Ma'lumotlar bazasiga ulanish")
    from app.core.database import AsyncSessionLocal, init_db
    from app.models.user import User
    from app.models.department import Department
    from app.models.camera import Camera
    from app.models.module import Module
    from sqlalchemy import select

    await init_db()
    print("   [OK] DB tayyor (jadval/ustunlar sinxronlandi)")

    async with AsyncSessionLocal() as db:
        # ====== 3. Bo'lim borligini ta'minlash ======
        step(3, "'eritish' bo'limini topish/yaratish")
        res = await db.execute(select(Department).where(Department.key == "eritish"))
        dept = res.scalar_one_or_none()
        if not dept:
            dept = Department(
                key="eritish", name="Eritish bo'limi",
                color="#ef4444", icon="flame",
            )
            db.add(dept)
            await db.flush()
            print(f"   [+] Yangi bo'lim yaratildi: 'eritish' (id={dept.id})")
        else:
            print(f"   [OK] Mavjud bo'lim: '{dept.key}' (id={dept.id})")

        # ====== 4. Modullarni yangilash ======
        step(4, "AI modullarni .pt fayllar bilan bog'lash")
        for mod_key, info in MODULE_TO_PT.items():
            res = await db.execute(select(Module).where(Module.key == mod_key))
            m = res.scalar_one_or_none()
            if not m:
                print(f"   [X] '{mod_key}' moduli DB da topilmadi - o'tkazib yuborildi")
                continue
            pt_path = copied.get(mod_key)
            if not pt_path:
                print(f"   [X] '{mod_key}' uchun .pt yo'q - faqat metadata yangilanmaydi")
                continue
            pt_file = Path(pt_path)
            size_mb = round(pt_file.stat().st_size / (1024 * 1024), 2)
            m.model_path = str(pt_file)
            m.model_filename = pt_file.name
            m.file_size_mb = size_mb
            m.architecture = info["arch"]
            m.model_version = info["version"]
            m.enabled = True
            m.updated_at = datetime.utcnow()
            # Class nomlarini ultralytics orqali olish
            try:
                from ultralytics import YOLO
                model = YOLO(str(pt_file))
                names = model.model.names if hasattr(model.model, 'names') else (model.names if hasattr(model, 'names') else {})
                if isinstance(names, dict):
                    class_names = [names[i] for i in sorted(names.keys())]
                else:
                    class_names = list(names) if names else []
                m.class_names = json.dumps(class_names, ensure_ascii=False)
                m.num_classes = len(class_names)
                print(f"   [+] '{mod_key:10s}' -> {pt_file.name:22s} ({size_mb} MB, {len(class_names)} ta klass)")
            except Exception as e:
                print(f"   [+] '{mod_key:10s}' -> {pt_file.name:22s} ({size_mb} MB, klasslar olinmadi: {e})")
        await db.commit()

        # ====== 5. Kameralarni qo'shish ======
        step(5, "4 ta Hikvision kamerani qo'shish")
        for cam_info in CAMERAS:
            ch = cam_info["channel"]
            # Hikvision NVR kanal raqami: 1-kamera = 101, 2-kamera = 201, va h.k.
            stream_id = f"{ch}01"
            rtsp_url = f"rtsp://{NVR_USER}:{NVR_PASS}@{NVR_IP}:{NVR_PORT}/Streaming/Channels/{stream_id}"

            # Mavjud bo'lsa - update, bo'lmasa - insert
            res = await db.execute(select(Camera).where(Camera.rtsp_url == rtsp_url))
            cam = res.scalar_one_or_none()
            if cam:
                print(f"   [OK] Kanal {ch:2d}: mavjud (id={cam.id}) - modullar yangilandi")
                cam.name = cam_info["name"]
                cam.location = cam_info["location"]
                cam.ip = NVR_IP
                cam.modules_enabled = DEFAULT_MODULES_PER_CAMERA.copy()
                cam.enabled = True
                cam.online = True
                cam.department_id = dept.id
            else:
                cam = Camera(
                    name=cam_info["name"],
                    location=cam_info["location"],
                    rtsp_url=rtsp_url,
                    ip=NVR_IP,
                    onvif_user=NVR_USER,
                    modules_enabled=DEFAULT_MODULES_PER_CAMERA.copy(),
                    confidence_threshold=0.65,
                    cooldown_sec=60,
                    enabled=True,
                    online=True,
                    department_id=dept.id,
                )
                db.add(cam)
                await db.flush()
                print(f"   [+] Kanal {ch:2d}: yangi qo'shildi (id={cam.id})")
            print(f"        URL: rtsp://admin:***@{NVR_IP}:{NVR_PORT}/Streaming/Channels/{stream_id}")
            print(f"        Modullar: {', '.join(DEFAULT_MODULES_PER_CAMERA)}")

        await db.commit()

    # ====== 6. Xulosa ======
    step(6, "TAYYOR")
    print(f"   {len(CAMERAS)} ta kamera DB ga qo'shildi/yangilandi")
    print(f"   {len([k for k,v in copied.items() if v])} ta .pt fayl bog'landi")
    print(f"   Har kameraga {len(DEFAULT_MODULES_PER_CAMERA)} ta AI modul biriktirildi")
    print()
    print("   Endi backendni qayta ishga tushiring:")
    print("     1. Terminal'da Ctrl+C bilan to'xtating")
    print("     2. 2_start_backend.bat ni ikki marta bosing")
    print()
    print("   Backend ishga tushgach, AI inference workerlar")
    print("   30 soniya ichida avtomatik boshlanadi va kameralarga ulanadi.")
    print()
    print("   Brauzerda:")
    print("     http://localhost:5000/cameras.html  - kameralar ro'yxati")
    print("     http://localhost:5000/modules.html  - modullar holati")
    print("     http://localhost:5000/events.html   - hodisalar")
    print("=" * 64)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[!] To'xtatildi")
        sys.exit(1)
    except Exception as e:
        print(f"\n[X] XATO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
