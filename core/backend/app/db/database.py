import asyncio

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
    """Create all tables on startup, then run pending Alembic migrations
    (Fase 12 §14 — substitui a whitelist ad-hoc que existia aqui)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    from app.db import migrations
    # upgrade_head() é síncrona (Alembic roda asyncio.run() internamente em
    # alembic/env.py) — não pode ser chamada de dentro de um event loop já
    # rodando, daí a thread separada.
    await asyncio.to_thread(migrations.upgrade_head)
