import asyncio
import sys

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.settings import settings


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


# TD-010: sob pytest, cada `with TestClient(app)` roda num event loop novo,
# mas o pool padrão do SQLAlchemy reaproveita conexões aiosqlite entre
# checkouts — uma conexão nascida no loop de um teste anterior (já fechado)
# quebra com "Event loop is closed"/"database is locked" num teste posterior.
# NullPool garante conexão nova a cada checkout, eliminando o reaproveitamento
# cross-loop. Produção não é afetada (loop único, processo único).
_pool_kwargs = {}
if "pytest" in sys.modules:
    from sqlalchemy.pool import NullPool
    _pool_kwargs["poolclass"] = NullPool

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
    **_pool_kwargs,
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
