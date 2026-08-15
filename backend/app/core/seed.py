"""Seed the database with sample data on first startup"""
from sqlalchemy import select
from datetime import datetime, timedelta
import random

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.department import Department
from app.models.camera import Camera
from app.models.module import Module
from app.models.user import User
from app.models.event import Event


DEPARTMENTS = [
    {"key": "eritish", "name": "Eritish bolimi", "color": "#ef4444", "icon": "flame"},
    {"key": "pechka", "name": "Pechkaxona", "color": "#f97316", "icon": "thermometer"},
    {"key": "ombor", "name": "Ombor", "color": "#3b82f6", "icon": "package"},
    {"key": "quyish", "name": "Quyish bolimi", "color": "#ec4899", "icon": "droplet"},
    {"key": "mexanik", "name": "Mexanik ustaxona", "color": "#8b5cf6", "icon": "wrench"},
    {"key": "ofis", "name": "Ofis", "color": "#10b981", "icon": "briefcase"},
]

MODULES = [
    {"key": "helmet", "name": "Kaska Aniqlash",
     "description": "Ishchilar himoya kaskasini kiyganini avtomatik aniqlaydi.",
     "model_path": "", "model_version": "v1",
     "confidence_threshold": 0.65, "priority": "normal",
     "icon": "hard-hat", "color": "#3b82f6", "is_custom": False, "enabled": True},
    {"key": "phone", "name": "Telefon Aniqlash",
     "description": "Ish vaqtida telefon ishlatishni nazorat qiladi.",
     "model_path": "", "model_version": "v1",
     "confidence_threshold": 0.70, "priority": "low",
     "icon": "smartphone", "color": "#8b5cf6", "is_custom": False, "enabled": True},
    {"key": "smoking", "name": "Chekish Aniqlash",
     "description": "Yong'in xavfini kamaytirish uchun chekishni aniqlaydi.",
     "model_path": "", "model_version": "v1",
     "confidence_threshold": 0.60, "priority": "high",
     "icon": "cigarette-off", "color": "#ec4899", "is_custom": False, "enabled": True},
    {"key": "fall", "name": "Yiqilish Aniqlash",
     "description": "Yiqilgan yoki harakatsiz ishchini aniqlaydi.",
     "model_path": "", "model_version": "v1",
     "confidence_threshold": 0.70, "priority": "critical",
     "icon": "user-x", "color": "#f59e0b", "is_custom": False, "enabled": True},
    {"key": "fire", "name": "Yong'in",
     "description": "Dastlabki olov belgilarini aniqlaydi (kritik ogohlantirish).",
     "model_path": "", "model_version": "v1",
     "confidence_threshold": 0.55, "priority": "critical",
     "icon": "flame", "color": "#ef4444", "is_custom": False, "enabled": True},
    {"key": "smoke", "name": "Tutun Aniqlash",
     "description": "Yong'indan oldingi tutun belgilarini aniqlaydi.",
     "model_path": "", "model_version": "v1",
     "confidence_threshold": 0.55, "priority": "high",
     "icon": "cloud-fog", "color": "#94a3b8", "is_custom": False, "enabled": True},
    {"key": "zone", "name": "Cheklangan Zona",
     "description": "Polygon orqali belgilangan taqiqlangan zonalarga kirishni aniqlaydi.",
     "model_path": "", "model_version": "v1",
     "confidence_threshold": 0.60, "priority": "high",
     "icon": "shield-x", "color": "#06b6d4", "is_custom": False, "enabled": True},
    {"key": "twoperson", "name": "Two-Person Rule",
     "description": "Xavfli operatsiyalarda yolg'iz ishlash taqiqlanadi.",
     "model_path": "", "model_version": "v1",
     "confidence_threshold": 0.65, "priority": "high",
     "icon": "users-2", "color": "#10b981", "is_custom": False, "enabled": False},
]

CAMERAS = [
    ("Eritish-1 Kirish", "eritish", "Garbiy eshik", "192.168.1.101", ["helmet", "fire", "zone"], True),
    ("Eritish-2 Asosiy pech", "eritish", "Shimoliy burchak", "192.168.1.102", ["helmet", "fire", "zone", "fall"], True),
    ("Eritish-3 Quyish zonasi", "eritish", "Janub-sharq", "192.168.1.103", ["helmet", "fire", "fall"], True),
    ("Pechka-1", "pechka", "Asosiy zal", "192.168.1.104", ["helmet", "smoking", "fire"], True),
    ("Pechka-2", "pechka", "Shimoliy", "192.168.1.105", ["helmet", "smoking", "fire", "fall"], True),
    ("Pechka-3", "pechka", "Markaziy", "192.168.1.106", ["helmet", "fire"], True),
    ("Pechka-4 Chiqish", "pechka", "Sharqiy chiqish", "192.168.1.107", ["helmet", "fire", "zone"], True),
    ("Ombor-1", "ombor", "Asosiy ombor", "192.168.1.108", ["fall", "phone", "zone"], True),
    ("Ombor-2 Yuk maydoni", "ombor", "Yuk eshigi", "192.168.1.109", ["fall", "phone"], True),
    ("Quyish-1", "quyish", "Asosiy", "192.168.1.110", ["helmet", "fire", "fall"], True),
    ("Quyish-2", "quyish", "Quyish kanali", "192.168.1.111", ["helmet", "fire", "zone"], False),
    ("Mexanik-1", "mexanik", "Ustaxona", "192.168.1.112", ["helmet", "phone"], True),
    ("Mexanik-2", "mexanik", "Stanok zonasi", "192.168.1.113", ["helmet", "phone", "zone"], True),
    ("Ofis-Koridor", "ofis", "Asosiy koridor", "192.168.1.114", ["fire"], True),
]

# Only ONE admin is seeded. Other users are added by admin via UI.
USERS = [
    ("mardonbek", "mardonbeksulaymonqulov156@gmail.com", "Mardonbek Sulaymonqulov", "admin", "admin123"),
]

EVENT_TEMPLATES = [
    ("fire", "Yongin belgilari aniqlandi", True),
    ("smoking", "Chekish aniqlandi", True),
    ("helmet", "Kaska kiyilmagan", False),
    ("phone", "Telefon ishlatish", False),
    ("zone", "Cheklangan zonaga kirish", True),
    ("fall", "Yiqilish aniqlandi", True),
]


async def seed_if_empty():
    async with AsyncSessionLocal() as db:
        existing = (await db.execute(select(Department))).scalars().first()
        if existing:
            print("[Seed] Database already populated, skipping.")
            return

        print("[Seed] Populating database with sample data...")

        dept_map = {}
        for d in DEPARTMENTS:
            dept = Department(**d)
            db.add(dept)
            await db.flush()
            dept_map[d["key"]] = dept.id

        for m in MODULES:
            # Provide safe defaults for fields not in legacy dicts
            payload = {
                "model_filename": "",
                "architecture": "",
                "file_size_mb": 0.0,
                "class_names": "[]",
                "num_classes": 0,
                "image_url": "",
                "is_custom": False,
                "total_detections": 0,
                "avg_inference_ms": 0.0,
                "accuracy_pct": 0.0,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                **m,
            }
            db.add(Module(**payload))

        cam_ids = []
        for name, dept_key, loc, ip, mods, online in CAMERAS:
            cam = Camera(
                name=name, location=loc,
                rtsp_url=f"rtsp://{ip}:554/Streaming/Channels/101",
                ip=ip, modules_enabled=mods, online=online,
                department_id=dept_map[dept_key],
                confidence_threshold=0.65, cooldown_sec=60,
            )
            db.add(cam)
            await db.flush()
            cam_ids.append(cam.id)

        for username, email, full_name, role, password in USERS:
            db.add(User(
                username=username, email=email, full_name=full_name,
                role=role, password_hash=hash_password(password),
                last_seen=datetime.utcnow(),
            ))

        now = datetime.utcnow()
        for _ in range(120):
            module, msg, critical = random.choice(EVENT_TEMPLATES)
            hours_ago = random.randint(0, 7 * 24)
            db.add(Event(
                camera_id=random.choice(cam_ids),
                module_name=module,
                message=msg,
                confidence=random.uniform(0.65, 0.98),
                critical=critical and random.random() > 0.3,
                timestamp=now - timedelta(hours=hours_ago, minutes=random.randint(0, 59)),
                acknowledged=random.random() > 0.5,
            ))

        await db.commit()
        print(f"[Seed] Done: {len(DEPARTMENTS)} depts, {len(CAMERAS)} cameras, "
              f"{len(MODULES)} modules, {len(USERS)} admin user, 120 events.")
        print(f"[Seed] Admin login: {USERS[0][1]}")
