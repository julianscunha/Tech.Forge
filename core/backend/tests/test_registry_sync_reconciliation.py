"""Regressão: sync_registry_to_db() só fazia upsert, nunca removia linha
órfã da tabela `modules` — um módulo removido do disco (ou resíduo de
teste escrito direto no banco) ficava contado pra sempre nos cards do
Dashboard (`modules_installed`/`modules_enabled`), divergindo da
realidade (registry/disco).
"""
from __future__ import annotations

from datetime import datetime

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.registry import Module
from app.module_engine.enums import ModuleStatus
from app.module_engine.registry import ModuleEntry
from app.services.registry_sync import sync_registry_to_db

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture()
async def db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as session:
        yield session
    await engine.dispose()


def _entry(module_id: str) -> ModuleEntry:
    return ModuleEntry(
        module_id=module_id, name=module_id, version="1.0.0",
        category="Test", vendor="V", author="A", description="d",
        status=ModuleStatus.INSTALLED, install_date=datetime.utcnow(),
    )


@pytest.mark.asyncio
async def test_removes_db_row_no_longer_in_registry(db, monkeypatch):
    # Linha "órfã" já na tabela — nunca foi removida do disco/registry,
    # mas continua no banco (exatamente o bug real observado em produção).
    db.add(Module(module_id="ghost", name="Ghost", version="1.0.0", is_enabled=True))
    await db.commit()

    fake_registry = type("R", (), {"all": staticmethod(lambda: [_entry("real_mod")])})()
    monkeypatch.setattr("app.services.registry_sync.registry", fake_registry)

    await sync_registry_to_db(db)

    from sqlalchemy import select
    rows = (await db.execute(select(Module.module_id))).scalars().all()
    assert set(rows) == {"real_mod"}


@pytest.mark.asyncio
async def test_empty_registry_clears_table(db, monkeypatch):
    db.add(Module(module_id="ghost", name="Ghost", version="1.0.0", is_enabled=True))
    await db.commit()

    fake_registry = type("R", (), {"all": staticmethod(lambda: [])})()
    monkeypatch.setattr("app.services.registry_sync.registry", fake_registry)

    await sync_registry_to_db(db)

    from sqlalchemy import select
    rows = (await db.execute(select(Module.module_id))).scalars().all()
    assert rows == []
