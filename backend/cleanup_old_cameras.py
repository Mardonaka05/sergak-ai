"""
Eski soxta kameralarni (seed paytidagi 192.168.1.x IP) tozalash.
Faqat haqiqiy 192.168.5.10 NVR kameralarini qoldiradi.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


async def main():
    from app.core.database import AsyncSessionLocal
    from app.models.camera import Camera
    from app.models.event import Event
    from sqlalchemy import select, delete

    print("=" * 60)
    print("  Eski soxta kameralarni tozalash")
    print("=" * 60)

    async with AsyncSessionLocal() as db:
        # Barcha kameralarni olish
        res = await db.execute(select(Camera).order_by(Camera.id))
        cameras = res.scalars().all()

        to_delete = []
        to_keep = []
        for c in cameras:
            if "192.168.5.10" in (c.rtsp_url or "") or "192.168.5.10" in (c.ip or ""):
                to_keep.append(c)
            else:
                to_delete.append(c)

        print(f"\n  Saqlanadi (haqiqiy):  {len(to_keep)} ta")
        for c in to_keep:
            print(f"    [+] id={c.id:3d}  {c.name}")

        print(f"\n  O'chiriladi (soxta):   {len(to_delete)} ta")
        for c in to_delete:
            print(f"    [-] id={c.id:3d}  {c.name}  ({c.ip or 'no IP'})")

        if not to_delete:
            print("\n  Hech narsa o'chirilmaydi.")
            return

        print("\n  3 soniya kutish... (Ctrl+C bilan to'xtatish mumkin)")
        await asyncio.sleep(3)

        # Avval shu kameralarning event'larini o'chirish
        cam_ids = [c.id for c in to_delete]
        if cam_ids:
            del_events = await db.execute(
                delete(Event).where(Event.camera_id.in_(cam_ids))
            )
            print(f"\n  [-] {del_events.rowcount} ta eski event o'chirildi")

        # Endi kameralarni o'chirish
        for c in to_delete:
            await db.delete(c)
        await db.commit()

        print(f"  [-] {len(to_delete)} ta soxta kamera o'chirildi")
        print(f"\n  [OK] Endi faqat haqiqiy {len(to_keep)} ta kamera qoldi")
        print()
        print("  Backendni qayta ishga tushiring - workerlar ham qayta sozlanadi.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
