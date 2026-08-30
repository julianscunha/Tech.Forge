"""
TechForge Fase 14 Slice 10 — Error Registry
==============================================
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
from app.models.error_registry import ErrorRecord
from app.services.error_registry import ErrorRegistryService

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture()
async def db_session(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{(tmp_path / 'errors.db').as_posix()}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as session:
        yield session
    await engine.dispose()


class TestRecord:

    @pytest.mark.asyncio
    async def test_record_persists_entry(self, db_session):
        entry = await ErrorRegistryService.record(
            db_session, source="execution", message="boom", module_id="hello_world",
            execution_id="exec-1", detail="ValueError: boom",
        )
        assert entry.id is not None
        assert entry.source == "execution"
        assert entry.module_id == "hello_world"

    @pytest.mark.asyncio
    async def test_module_and_execution_id_optional(self, db_session):
        entry = await ErrorRegistryService.record(db_session, source="runtime", message="component died")
        assert entry.module_id is None
        assert entry.execution_id is None


class TestListing:

    @pytest.mark.asyncio
    async def test_recent_orders_newest_first(self, db_session):
        await ErrorRegistryService.record(db_session, source="runtime", message="a")
        await ErrorRegistryService.record(db_session, source="runtime", message="b")
        results = await ErrorRegistryService.recent(db_session)
        assert results[0].message == "b"

    @pytest.mark.asyncio
    async def test_list_for_module_filters(self, db_session):
        await ErrorRegistryService.record(db_session, source="execution", message="a", module_id="mod_a")
        await ErrorRegistryService.record(db_session, source="execution", message="b", module_id="mod_b")
        results = await ErrorRegistryService.list_for_module(db_session, "mod_a")
        assert len(results) == 1
        assert results[0].module_id == "mod_a"


class TestCleanup:

    @pytest.mark.asyncio
    async def test_cleanup_removes_old_entries(self, db_session):
        entry = await ErrorRegistryService.record(db_session, source="runtime", message="old")
        old_date = datetime.utcnow() - timedelta(days=100)
        await db_session.execute(
            update(ErrorRecord).where(ErrorRecord.id == entry.id).values(created_at=old_date)
        )
        await db_session.commit()
        removed = await ErrorRegistryService.cleanup_old(db_session, retention_days=90)
        assert removed == 1


class TestCaptureErrorWiring:
    """capture_error()/capture_error_async() ligados nos 3 pontos reais."""

    def test_invoker_captures_execution_failure(self, monkeypatch, tmp_path):
        from app.core import settings as settings_module
        from app.db import database as db_module

        engine_url = f"sqlite+aiosqlite:///{(tmp_path / 'invoke_errors.db').as_posix()}"
        monkeypatch.setattr(settings_module.settings, "DATABASE_URL", engine_url)

        import asyncio
        test_engine = create_async_engine(engine_url)

        async def _prep():
            async with test_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        asyncio.run(_prep())

        Session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
        monkeypatch.setattr(db_module, "AsyncSessionLocal", Session)

        from app.service_registry import invoker
        from app.service_registry.descriptor import ServiceStatus
        from app.service_registry.errors import ServiceExecutionFailedError

        class FakeExport:
            name = "boom"
            parameters = []

        class FakeContract:
            exports = [FakeExport()]

        class FakeDescriptor:
            module_id = "hello_world"
            status = ServiceStatus.ACTIVE
            contract = FakeContract()

        def _raise():
            raise ValueError("kaboom")

        monkeypatch.setattr(invoker.service_registry, "find_service", lambda sid: FakeDescriptor())
        monkeypatch.setattr(invoker, "_load_export_callable", lambda mid, name: _raise)

        with pytest.raises(ServiceExecutionFailedError):
            invoker.invoke("hello_world", "boom")

        async def _check():
            async with Session() as session:
                return await ErrorRegistryService.recent(session)
        results = asyncio.run(_check())
        assert len(results) == 1
        assert results[0].source == "execution"
        assert results[0].module_id == "hello_world"

        asyncio.run(test_engine.dispose())

    def test_runtime_degraded_captures_error(self, monkeypatch, tmp_path):
        from app.core import settings as settings_module
        from app.db import database as db_module

        engine_url = f"sqlite+aiosqlite:///{(tmp_path / 'runtime_errors.db').as_posix()}"
        monkeypatch.setattr(settings_module.settings, "DATABASE_URL", engine_url)

        import asyncio
        test_engine = create_async_engine(engine_url)

        async def _prep():
            async with test_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        asyncio.run(_prep())

        Session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
        monkeypatch.setattr(db_module, "AsyncSessionLocal", Session)

        from app.runtime import TechForgeRuntime, RuntimeState
        rt = TechForgeRuntime()
        rt.state = RuntimeState.READY
        rt.register_component_pid("fake", 999_999_999)
        rt.check_liveness()

        async def _check():
            async with Session() as session:
                return await ErrorRegistryService.recent(session)
        results = asyncio.run(_check())
        assert len(results) == 1
        assert results[0].source == "runtime"

        asyncio.run(test_engine.dispose())

    def test_install_with_invalid_dependency_captures_error(self, tmp_path, monkeypatch):
        from app.core import settings as settings_module
        from app.db import database as db_module

        engine_url = f"sqlite+aiosqlite:///{(tmp_path / 'dep_errors.db').as_posix()}"
        monkeypatch.setattr(settings_module.settings, "DATABASE_URL", engine_url)

        import asyncio
        test_engine = create_async_engine(engine_url)

        async def _prep():
            async with test_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        asyncio.run(_prep())

        Session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
        monkeypatch.setattr(db_module, "AsyncSessionLocal", Session)

        from tests.test_phase4 import MANIFEST_BASE, make_mod_file, make_package_manager
        from app.package_manager.enums import InstallStatus

        pm = make_package_manager(tmp_path)
        manifest = {**MANIFEST_BASE, "dependencies": [{"target": {}}]}
        mod = make_mod_file(tmp_path, manifest)

        result = asyncio.run(pm.install(mod))
        assert result.status == InstallStatus.FAILED

        async def _check():
            async with Session() as session:
                return await ErrorRegistryService.recent(session)
        results = asyncio.run(_check())
        assert len(results) == 1
        assert results[0].source == "dependency"
        assert results[0].module_id == "test_pkg"

        asyncio.run(test_engine.dispose())
