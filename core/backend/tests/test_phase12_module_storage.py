"""Fase 12 Slice 5 — Module Storage API (key-value), spec §6/§7.

`context.storage` — get/set/transaction, isolado por module_id (fixado na
construção, nunca argumento de chamada — um módulo não consegue ler/
escrever chave de outro módulo mesmo por engano).

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase12_module_storage.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))

from app.db.database import Base
from app.models.module_kv_store import ModuleKVStoreRow  # noqa: F401 — registra a tabela
from app.services.module_storage import ModuleKVStorage, ModuleStorageError


@pytest_asyncio.fixture()
async def session_factory(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{(tmp_path / 'kv.db').as_posix()}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest.mark.asyncio
async def test_get_returns_default_when_key_absent(session_factory):
    storage = ModuleKVStorage("mod_a", session_factory=session_factory)
    assert await storage.get("missing") is None
    assert await storage.get("missing", default="fallback") == "fallback"


@pytest.mark.asyncio
async def test_set_then_get_round_trips_json_serializable_value(session_factory):
    storage = ModuleKVStorage("mod_a", session_factory=session_factory)
    await storage.set("count", 3)
    await storage.set("nested", {"a": [1, 2, 3]})
    assert await storage.get("count") == 3
    assert await storage.get("nested") == {"a": [1, 2, 3]}


@pytest.mark.asyncio
async def test_set_overwrites_existing_key(session_factory):
    storage = ModuleKVStorage("mod_a", session_factory=session_factory)
    await storage.set("count", 1)
    await storage.set("count", 2)
    assert await storage.get("count") == 2


@pytest.mark.asyncio
async def test_set_rejects_non_json_serializable_value_with_typed_error(session_factory):
    storage = ModuleKVStorage("mod_a", session_factory=session_factory)
    with pytest.raises(ModuleStorageError):
        await storage.set("bad", object())


@pytest.mark.asyncio
async def test_modules_are_isolated_from_each_other(session_factory):
    a = ModuleKVStorage("mod_a", session_factory=session_factory)
    b = ModuleKVStorage("mod_b", session_factory=session_factory)
    await a.set("shared_key", "from_a")
    assert await b.get("shared_key") is None
    assert await a.get("shared_key") == "from_a"


@pytest.mark.asyncio
async def test_transaction_commits_all_writes_on_clean_exit(session_factory):
    storage = ModuleKVStorage("mod_a", session_factory=session_factory)
    async with storage.transaction() as tx:
        await tx.set("x", 1)
        await tx.set("y", 2)
    assert await storage.get("x") == 1
    assert await storage.get("y") == 2


@pytest.mark.asyncio
async def test_transaction_rolls_back_all_writes_on_exception(session_factory):
    storage = ModuleKVStorage("mod_a", session_factory=session_factory)
    await storage.set("x", "original")
    with pytest.raises(RuntimeError):
        async with storage.transaction() as tx:
            await tx.set("x", "changed")
            raise RuntimeError("boom")
    assert await storage.get("x") == "original"


def test_module_execution_context_build_binds_storage_to_own_module_id():
    """`ModuleExecutionContext.build()` nunca deixa o módulo escolher seu
    próprio module_id no storage — isolamento é estrutural (Fase 12 §6)."""
    from fastapi.testclient import TestClient

    from app.main import app
    from app.module_runtime.context import ModuleExecutionContext
    from app.module_engine.registry import registry as module_registry

    with TestClient(app):
        ctx = ModuleExecutionContext.build("hello_world", module_registry)
    assert ctx is not None
    assert isinstance(ctx.storage, ModuleKVStorage)
    assert ctx.storage._module_id == "hello_world"
