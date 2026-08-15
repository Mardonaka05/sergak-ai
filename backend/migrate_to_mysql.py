"""SQLite -> MySQL migratsiya skripti.

Mavjud sergak.db faylidan barcha jadvallarni o'qib, OpenServer'dagi MySQL bazasiga
ko'chiradi. Faqat bir marta ishlatiladi.

ISHLATISH:
    1. OpenServer'da PHPMyAdmin'ga kiring (odatda http://localhost/phpmyadmin/)
    2. Yangi baza yarating: nomi `sergak_ai`, salom: utf8mb4_unicode_ci
    3. Quyidagi paketlarni o'rnating:
         pip install aiomysql cryptography
    4. Backend papkasidan ishga tushiring:
         cd "backend"
         python migrate_to_mysql.py
    5. Skriptdagi MYSQL_URL sozlamani o'zgartirib qo'ying (parol bo'lsa)
    6. Migratsiya muvaffaqiyatli bo'lgach .env faylida DB_URL ni MySQL ga o'zgartiring
       va backendni qayta ishga tushiring.
"""
import asyncio
import os
import sys
from pathlib import Path

# ============ SOZLAMALAR ============
# OpenServer'dagi MySQL ulanishi. Standart sozlamalar — root, parol yo'q.
# Agar boshqa bo'lsa, bu yerni o'zgartiring:
MYSQL_HOST     = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT     = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER     = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DB       = os.getenv("MYSQL_DB", "sergak_ai")

SQLITE_PATH = Path(__file__).parent / "sergak.db"
# =====================================

SQLITE_URL = f"sqlite+aiosqlite:///{SQLITE_PATH}"
MYSQL_URL = (
    f"mysql+aiomysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    f"?charset=utf8mb4"
)

# Make sure local imports work
sys.path.insert(0, str(Path(__file__).resolve().parent))


async def main():
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select

    print("=" * 64)
    print("  SQLite -> MySQL migratsiyasi")
    print("=" * 64)
    print(f"  Manba:    {SQLITE_PATH}")
    print(f"  Maqsad:   mysql://{MYSQL_USER}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}")
    print("=" * 64)

    if not SQLITE_PATH.exists():
        print(f"\n[!] Xato: SQLite fayl topilmadi: {SQLITE_PATH}")
        print("    Hozircha ma'lumot yo'q. Backend kamida bir marta ishga tushishi kerak.")
        sys.exit(1)

    # Import models — bu Base.metadata ga jadvallarni ro'yxatdan o'tkazadi
    print("\n[1/5] Modellar yuklanmoqda...")
    # Avval config ni SQLite ga sozlaymiz (model importi uchun)
    import os
    os.environ["DB_URL"] = SQLITE_URL

    from app.core.database import Base
    from app.models import user, camera, department, event, module, chat  # noqa: F401
    print(f"      {len(Base.metadata.tables)} ta jadval topildi: {list(Base.metadata.tables.keys())}")

    # 2. SQLite engine
    print("\n[2/5] SQLite ga ulanmoqda...")
    src_engine = create_async_engine(SQLITE_URL, echo=False)
    src_session_factory = sessionmaker(src_engine, class_=AsyncSession, expire_on_commit=False)

    # 3. MySQL engine — avval ulanishni tekshiramiz
    print("\n[3/5] MySQL ga ulanmoqda...")
    try:
        dst_engine = create_async_engine(MYSQL_URL, echo=False, pool_pre_ping=True)
        async with dst_engine.begin() as conn:
            from sqlalchemy import text
            res = await conn.execute(text("SELECT VERSION()"))
            version = res.scalar()
            print(f"      MySQL versiyasi: {version}")
    except Exception as e:
        print(f"\n[!] MySQL ga ulanib bo'lmadi: {e}")
        print("\n    Tekshiring:")
        print("    1. OpenServer ishga tushganmi? (yashil tray ikonkasi)")
        print("    2. PHPMyAdmin'da 'sergak_ai' nomli baza yaratilganmi?")
        print(f"    3. MYSQL_USER='{MYSQL_USER}' va MYSQL_PASSWORD to'g'rimi?")
        print("    4. aiomysql va cryptography paketlari o'rnatilganmi?")
        print("       pip install aiomysql cryptography")
        sys.exit(1)
    dst_session_factory = sessionmaker(dst_engine, class_=AsyncSession, expire_on_commit=False)

    # 4. Jadval tuzilmalarini MySQL'da yaratamiz
    print("\n[4/5] MySQL'da jadval tuzilmalari yaratilmoqda...")
    async with dst_engine.begin() as conn:
        # Eski jadvallarni o'chiramiz (toza ko'chirish uchun)
        await conn.run_sync(Base.metadata.drop_all)
        # Yangidan yaratamiz
        await conn.run_sync(Base.metadata.create_all)
    print(f"      {len(Base.metadata.tables)} ta jadval yaratildi.")

    # 5. Ma'lumotlarni ko'chirish
    print("\n[5/5] Ma'lumotlar ko'chirilmoqda...\n")

    # Modellarni import qilamiz
    from app.models.user import User
    from app.models.department import Department
    from app.models.module import Module
    from app.models.camera import Camera
    from app.models.event import Event
    from app.models.chat import Conversation, ConversationMember, Message

    # Ko'chirish tartibi muhim — foreign key'lar sababli
    MODEL_ORDER = [
        ("departments",   Department),
        ("users",         User),
        ("modules",       Module),
        ("cameras",       Camera),
        ("events",        Event),
        ("conversations", Conversation),
        ("conversation_members", ConversationMember),
        ("messages",      Message),
    ]

    total = 0
    skipped_tables = []

    async with src_session_factory() as src_session, dst_session_factory() as dst_session:
        for label, ModelClass in MODEL_ORDER:
            try:
                # Manbadan o'qiymiz
                res = await src_session.execute(select(ModelClass))
                rows = res.scalars().all()
                count = len(rows)
                if count == 0:
                    print(f"      [{label:22s}]  bo'sh — o'tkazib yuborildi")
                    continue

                # Maqsad bazaga yozamiz — har bir qatorni yangi instance qilib
                for r in rows:
                    # __dict__ dan SQLAlchemy ichki maydonlarini olib tashlash
                    data = {c.name: getattr(r, c.name) for c in ModelClass.__table__.columns}
                    new_row = ModelClass(**data)
                    dst_session.add(new_row)
                await dst_session.commit()
                print(f"      [{label:22s}]  {count} ta yozuv ko'chirildi  OK")
                total += count
            except Exception as e:
                print(f"      [{label:22s}]  XATO: {e}")
                skipped_tables.append(label)
                try:
                    await dst_session.rollback()
                except Exception:
                    pass

    await src_engine.dispose()
    await dst_engine.dispose()

    print("\n" + "=" * 64)
    print(f"  TAYYOR — jami {total} ta yozuv ko'chirildi")
    if skipped_tables:
        print(f"  Xatoli jadvallar: {', '.join(skipped_tables)}")
    print("=" * 64)
    print("\nKeyingi qadamlar:")
    print("  1. .env faylida DB_URL ni o'zgartiring:")
    print(f"     DB_URL=mysql+aiomysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4")
    print("  2. Backendni qayta ishga tushiring: python -m app.main")
    print("  3. PHPMyAdmin'da http://localhost/phpmyadmin/ orqali jadvallarni ko'rishingiz mumkin")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[!] Foydalanuvchi tomonidan to'xtatildi")
        sys.exit(1)
