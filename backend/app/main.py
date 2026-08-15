"""Sergak AI - Industrial Safety AI Platform - FastAPI main entry"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.core.config import settings
from app.core.database import init_db
from app.core.seed import seed_if_empty
from app.core import inference
from app.api import (
    cameras, departments, events, modules,
    users, discovery, settings as settings_api, auth, chat, nvr,
)


FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "=" * 60)
    print("  SERGAK AI - Industrial Safety Platform")
    print("=" * 60)
    print("  [start] Initializing database...")
    await init_db()
    print("  [start] Seeding (if empty)...")
    await seed_if_empty()

    import asyncio as _aio
    inference.set_main_loop(_aio.get_event_loop())
    if inference.is_available():
        print("  [start] Inference engine: AVAILABLE (ultralytics + opencv)")
        _aio.create_task(inference.detection_writer_loop())
        async def _periodic_sync():
            while True:
                try:
                    await inference.sync_workers()
                except Exception as e:
                    print(f"[Inference] sync error: {e}")
                await _aio.sleep(30)
        _aio.create_task(_periodic_sync())
    else:
        print("  [start] Inference engine: DISABLED")

    print(f"  [ready] Server:   http://localhost:{settings.PORT}")
    print(f"  [ready] API docs: http://localhost:{settings.PORT}/docs")
    print(f"  [ready] Frontend: http://localhost:{settings.PORT}/")
    print("=" * 60 + "\n")
    yield
    print("[Sergak AI] Shutting down...")
    inference.stop_all()


app = FastAPI(
    title="Sergak AI",
    description="Industrial Safety AI Platform",
    version="2.1.4",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def no_cache_for_frontend(request, call_next):
    response = await call_next(request)
    path = request.url.path
    if path.startswith("/assets") or path.endswith(".html") or path == "/":
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(cameras.router, prefix="/api/cameras", tags=["cameras"])
app.include_router(departments.router, prefix="/api/departments", tags=["departments"])
app.include_router(events.router, prefix="/api/events", tags=["events"])
app.include_router(modules.router, prefix="/api/modules", tags=["modules"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(discovery.router, prefix="/api/discovery", tags=["discovery"])
app.include_router(nvr.router, prefix="/api/discovery", tags=["nvr"])
app.include_router(settings_api.router, prefix="/api/settings", tags=["settings"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "2.1.4", "service": "Sergak AI"}


@app.get("/", include_in_schema=False)
async def serve_root():
    f = FRONTEND_DIR / "index.html"
    if f.exists():
        return FileResponse(str(f), media_type="text/html")
    raise HTTPException(404, detail="Frontend not installed")


@app.get("/{page_name}.html", include_in_schema=False)
async def serve_page(page_name: str):
    f = FRONTEND_DIR / f"{page_name}.html"
    if f.exists():
        return FileResponse(str(f), media_type="text/html")
    raise HTTPException(404, detail=f"Page {page_name}.html not found")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(__file__, status_code=204)


if (FRONTEND_DIR / "assets").exists():
    app.mount(
        "/assets",
        StaticFiles(directory=str(FRONTEND_DIR / "assets")),
        name="assets",
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
