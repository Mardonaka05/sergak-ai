"""Application configuration"""
import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

_BASE = Path(__file__).resolve().parent.parent.parent
_ENV = _BASE / ".env"

# Load .env into os.environ BEFORE Settings reads it
if _ENV.exists():
    load_dotenv(dotenv_path=str(_ENV), override=True)
    print(f"[Config] Loaded .env from: {_ENV}")
else:
    print(f"[Config] WARNING: .env not found at {_ENV}")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_ENV), env_file_encoding="utf-8", extra="ignore", case_sensitive=False)

    HOST: str = "0.0.0.0"
    PORT: int = 5000
    DEBUG: bool = True
    DB_URL: str = "sqlite+aiosqlite:///./sergak.db"
    BASE_DIR: Path = _BASE
    SNAPSHOTS_DIR: Path = _BASE / "snapshots"
    MODELS_DIR: Path = _BASE / "models_pt"
    INFERENCE_MODE: str = "fp16"
    FRAME_SKIP: int = 2
    MOTION_TRIGGERED: bool = True
    DEFAULT_CONFIDENCE: float = 0.65
    DEFAULT_COOLDOWN_SEC: int = 60
    NETWORK_SUBNET: str = "192.168.1.0/24"
    ONVIF_TIMEOUT: int = 5
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_DEFAULT_CHAT: str = ""
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    SMTP_USE_TLS: bool = True
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    SNAPSHOT_RETENTION_DAYS: int = 30
    VIDEO_RETENTION_DAYS: int = 14


settings = Settings()
print(f"[Config] GOOGLE_CLIENT_ID loaded: {'YES (' + settings.GOOGLE_CLIENT_ID[:30] + '...)' if settings.GOOGLE_CLIENT_ID else 'NO (empty)'}")
print(f"[Config] SMTP_USER loaded: {settings.SMTP_USER or 'NO'}")
settings.SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)
