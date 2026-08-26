from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.settings import settings


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """FastAPI dependency — yields a database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Create all tables on startup, then add columns missing from older DBs."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _migrate()


async def _migrate() -> None:
    """Lightweight column migration (SQLite) — create_all won't alter existing tables."""
    from sqlalchemy import text
    # Whitelist literal — never interpolate table names from external input.
    additions = {
        "modules": [
            ("source_type", "VARCHAR(16) NOT NULL DEFAULT 'local'"),
            ("source_location", "VARCHAR(512)"),
        ],
    }
    allowed_tables = {"modules"}
    async with engine.begin() as conn:
        for table, cols in additions.items():
            if table not in allowed_tables:
                continue
            existing = {
                row[1] for row in await conn.execute(text(f"PRAGMA table_info({table})"))
            }
            if not existing:
                continue
            for name, ddl in cols:
                if name not in existing:
                    await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))
