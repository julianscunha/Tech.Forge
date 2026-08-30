"""
TechForge Fase 14 Slice 9 — Execution History persistida
============================================================
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))

from app.db.database import Base
from app.models.execution_history import ExecutionHistory
from app.services.execution_history import ExecutionHistoryService

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture()
async def db_session(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{(tmp_path / 'exec_history.db').as_posix()}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as session:
        yield session
    await engine.dispose()


class TestRecord:

    @pytest.mark.asyncio
    async def test_record_persists_entry(self, db_session):
        entry = await ExecutionHistoryService.record(
            db_session, execution_id="exec-1", module_id="hello_world",
            status="SUCCESS", duration_seconds=1.5,
        )
        assert entry.id is not None
        assert entry.execution_id == "exec-1"
        assert entry.status == "SUCCESS"

    @pytest.mark.asyncio
    async def test_record_stores_error_summary_on_failure(self, db_session):
        entry = await ExecutionHistoryService.record(
            db_session, execution_id="exec-2", module_id="hello_world",
            status="FAILED", duration_seconds=0.2, error_summary="boom",
        )
        assert entry.error_summary == "boom"


class TestListing:

    @pytest.mark.asyncio
    async def test_list_for_module_filters_by_module(self, db_session):
        await ExecutionHistoryService.record(db_session, execution_id="a", module_id="mod_a",
                                             status="SUCCESS", duration_seconds=0.1)
        await ExecutionHistoryService.record(db_session, execution_id="b", module_id="mod_b",
                                             status="SUCCESS", duration_seconds=0.1)
        results = await ExecutionHistoryService.list_for_module(db_session, "mod_a")
        assert len(results) == 1
        assert results[0].module_id == "mod_a"

    @pytest.mark.asyncio
    async def test_recent_orders_newest_first(self, db_session):
        await ExecutionHistoryService.record(db_session, execution_id="a", module_id="mod_a",
                                             status="SUCCESS", duration_seconds=0.1)
        await ExecutionHistoryService.record(db_session, execution_id="b", module_id="mod_a",
                                             status="SUCCESS", duration_seconds=0.1)
        results = await ExecutionHistoryService.recent(db_session)
        assert results[0].execution_id == "b"

    @pytest.mark.asyncio
    async def test_recent_respects_limit(self, db_session):
        for i in range(5):
            await ExecutionHistoryService.record(db_session, execution_id=f"e{i}", module_id="mod_a",
                                                 status="SUCCESS", duration_seconds=0.1)
        results = await ExecutionHistoryService.recent(db_session, limit=2)
        assert len(results) == 2


class TestCleanup:

    @pytest.mark.asyncio
    async def test_cleanup_removes_entries_older_than_retention(self, db_session):
        entry = await ExecutionHistoryService.record(db_session, execution_id="old", module_id="mod_a",
                                                      status="SUCCESS", duration_seconds=0.1)
        old_date = datetime.utcnow() - timedelta(days=100)
        await db_session.execute(
            update(ExecutionHistory).where(ExecutionHistory.id == entry.id).values(created_at=old_date)
        )
        await db_session.commit()

        removed = await ExecutionHistoryService.cleanup_old(db_session, retention_days=90)

        assert removed == 1
        assert await ExecutionHistoryService.recent(db_session) == []

    @pytest.mark.asyncio
    async def test_cleanup_keeps_recent_entries(self, db_session):
        await ExecutionHistoryService.record(db_session, execution_id="fresh", module_id="mod_a",
                                             status="SUCCESS", duration_seconds=0.1)
        removed = await ExecutionHistoryService.cleanup_old(db_session, retention_days=90)
        assert removed == 0
        assert len(await ExecutionHistoryService.recent(db_session)) == 1


class TestInvokerPersistence:

    def test_successful_invoke_persists_history(self, monkeypatch, tmp_path):
        from app.core import settings as settings_module
        from app.db import database as db_module

        engine_url = f"sqlite+aiosqlite:///{(tmp_path / 'invoke_history.db').as_posix()}"
        monkeypatch.setattr(settings_module.settings, "DATABASE_URL", engine_url)

        import asyncio
        from sqlalchemy.ext.asyncio import create_async_engine
        test_engine = create_async_engine(engine_url)

        async def _prep():
            async with test_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        asyncio.run(_prep())

        Session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
        monkeypatch.setattr(db_module, "AsyncSessionLocal", Session)

        from app.service_registry import invoker
        from app.service_registry.descriptor import ServiceStatus

        class FakeExport:
            name = "ping"
            parameters = []

        class FakeContract:
            exports = [FakeExport()]

        class FakeDescriptor:
            module_id = "hello_world"
            status = ServiceStatus.ACTIVE
            contract = FakeContract()

        monkeypatch.setattr(invoker.service_registry, "find_service", lambda sid: FakeDescriptor())
        monkeypatch.setattr(invoker, "_load_export_callable", lambda mid, name: (lambda: "pong"))

        invoker.invoke("hello_world", "ping")

        async def _check():
            async with Session() as session:
                return await ExecutionHistoryService.recent(session)
        results = asyncio.run(_check())
        assert len(results) == 1
        assert results[0].module_id == "hello_world"
        assert results[0].status == "SUCCESS"

        asyncio.run(test_engine.dispose())
