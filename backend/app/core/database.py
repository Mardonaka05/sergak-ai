"""SQLAlchemy async database setup — supports SQLite and MySQL."""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text, inspect

from app.core.config import settings


class Base(DeclarativeBase):
    pass


# Build engine kwargs — pool settings useful for MySQL, ignored by SQLite
_engine_kwargs = {"echo": False, "future": True}
if settings.DB_URL.startswith("mysql"):
    # NOTE: pool_pre_ping=False because aiomysql 0.3+ changed ping() signature
    # and current SQLAlchemy version's adapter is not yet compatible.
    # Without pre-ping, aiomysql still auto-reconnects on broken connections.
    _engine_kwargs.update({
        "pool_size": 10, "max_overflow": 20,
        "pool_pre_ping": False, "pool_recycle": 3600,
    })

engine = create_async_engine(settings.DB_URL, **_engine_kwargs)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def _is_sqlite() -> bool:
    return settings.DB_URL.startswith("sqlite")


def _is_mysql() -> bool:
    return settings.DB_URL.startswith("mysql")


def _existing_columns(sync_conn, table_name: str):
    """Return set of column names for a table, or None if table doesn't exist.
    Works on SQLite, MySQL, PostgreSQL."""
    insp = inspect(sync_conn)
    if not insp.has_table(table_name):
        return None
    return {c["name"] for c in insp.get_columns(table_name)}


async def init_db():
    """Create all tables from models + run idempotent migrations (cross-DB)."""
    # Import all models so SQLAlchemy is aware of them
    from app.models import camera, department, event, user, module, chat  # noqa
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # ===== users migrations =====
        try:
            cols = await conn.run_sync(_existing_columns, "users")
            if cols is not None:
                bool_default = "0" if _is_sqlite() else "FALSE"
                user_migrations = [
                    ("pending", f"ALTER TABLE users ADD COLUMN pending BOOLEAN DEFAULT {bool_default}"),
                    ("requested_role", "ALTER TABLE users ADD COLUMN requested_role VARCHAR(20) DEFAULT 'operator'"),
                    ("request_reason", "ALTER TABLE users ADD COLUMN request_reason VARCHAR(500) DEFAULT ''"),
                    ("last_seen", "ALTER TABLE users ADD COLUMN last_seen DATETIME NULL"),
                    ("department_filter", "ALTER TABLE users ADD COLUMN department_filter VARCHAR(200) DEFAULT ''"),
                    ("avatar_url", "ALTER TABLE users ADD COLUMN avatar_url VARCHAR(500) DEFAULT ''"),
                ]
                for col, sql in user_migrations:
                    if col not in cols:
                        await conn.execute(text(sql))
                        print(f"[DB] Added column users.{col}")
        except Exception as e:
            print("[DB] users migration skipped:", e)

        # ===== modules migrations =====
        try:
            cols = await conn.run_sync(_existing_columns, "modules")
            if cols is not None:
                bool_default = "0" if _is_sqlite() else "FALSE"
                module_migrations = [
                    ("model_filename", "ALTER TABLE modules ADD COLUMN model_filename VARCHAR(200) DEFAULT ''"),
                    ("architecture", "ALTER TABLE modules ADD COLUMN architecture VARCHAR(40) DEFAULT ''"),
                    ("file_size_mb", "ALTER TABLE modules ADD COLUMN file_size_mb FLOAT DEFAULT 0.0"),
                    ("class_names", "ALTER TABLE modules ADD COLUMN class_names TEXT"),
                    ("num_classes", "ALTER TABLE modules ADD COLUMN num_classes INTEGER DEFAULT 0"),
                    ("image_url", "ALTER TABLE modules ADD COLUMN image_url VARCHAR(500) DEFAULT ''"),
                    ("is_custom", f"ALTER TABLE modules ADD COLUMN is_custom BOOLEAN DEFAULT {bool_default}"),
                    ("total_detections", "ALTER TABLE modules ADD COLUMN total_detections INTEGER DEFAULT 0"),
                    ("avg_inference_ms", "ALTER TABLE modules ADD COLUMN avg_inference_ms FLOAT DEFAULT 0.0"),
                    ("accuracy_pct", "ALTER TABLE modules ADD COLUMN accuracy_pct FLOAT DEFAULT 0.0"),
                    ("last_used_at", "ALTER TABLE modules ADD COLUMN last_used_at DATETIME NULL"),
                    ("created_at", "ALTER TABLE modules ADD COLUMN created_at DATETIME NULL"),
                    ("updated_at", "ALTER TABLE modules ADD COLUMN updated_at DATETIME NULL"),
                ]
                for col, sql in module_migrations:
                    if col not in cols:
                        await conn.execute(text(sql))
                        print(f"[DB] Added column modules.{col}")
        except Exception as e:
            print("[DB] modules migration skipped:", e)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
