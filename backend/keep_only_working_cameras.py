"""
Faqat ishlayotgan 2 ta kamerani qoldirish:
- CH 201 (Kamera-2 - Pechkaxona asosiy)
- CH 401 (Kamera-4 - Pechkaxona chiqish)

Boshqa hammasi o'chiriladi.
Qoladiganlariga 5 ta modul to'liq biriktiriladi.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

KEEP_CHANNELS = ["201", "401"]  # NVR kanal raqamlari
ALL_MODULES = ["helmet", "phone", "smoking", "fall", "fire"]


async def main():
    from app.core.database import AsyncSessionLocal
    from app.models.camera import Camera
    from app.models.event import Event
    from sqlalchemy import select, delete

    print("=" * 60)
    print(f"  Faqat CH {' va CH '.join(KEEP_CHANNELS)} qoldirish")
    print("=" * 60)

    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Camera).order_by(Camera.id))
        cameras = res.scalars().all()

        to_keep = []
        to_delete = []
        for c in cameras:
            url = c.rtsp_url or ""
            keep = any(f"Channels/{ch}" in url for ch in KEEP_CHANNELS)
            if keep:
                to_keep.append(c)
            else:
                to_delete.append(c)

        print(f"\n  Saqlanadi: {len(to_keep)} ta")
        for c in to_keep:
            ch = "?"
            import re
            m = re.search(r"Channels/(\d+)", c.rtsp_url or "")
            if m: ch = m.group(1)
            print(f"    [+] id={c.id:3d}  CH {ch}  {c.name}")

        print(f"\n  O'chiriladi: {len(to_delete)} ta")
        for c in to_delete:
            print(f"    [-] id={c.id:3d}  {c.name}")

        if not to_delete and not to_keep:
            print("\n  Hech qanday kamera yo'q.")
            return

        if to_delete:
            print("\n  3 soniya kutish... (Ctrl+C bilan bekor qilish)")
            await asyncio.sleep(3)

            cam_ids = [c.id for c in to_delete]
            del_events = await db.execute(
                delete(Event).where(Event.camera_id.in_(cam_ids))
            )
            print(f"\n  [-] {del_events.rowcount} ta event o'chirildi")

            for c in to_delete:
                await db.delete(c)
            await db.commit()
            print(f"  [-] {len(to_delete)} ta kamera o'chirildi")

        # Qolganlariga to'liq modullar biriktirish
        if to_keep:
            print("\n  5 ta modulni biriktirish:")
            for c in to_keep:
                c.modules_enabled = ALL_MODULES.copy()
                c.enabled = True
                c.online = True
                print(f"    [+] id={c.id} -> {', '.join(ALL_MODULES)}")
            await db.commit()

        print(f"\n  [OK] Tayyor — endi faqat {len(to_keep)} ta kamera bor")
        print("       Backendni qayta ishga tushiring")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
