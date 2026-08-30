"""
TechForge Fase 14 Slice 17 (parte 1) — Notifications integration
===================================================================
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))

from fastapi.testclient import TestClient

from app.main import app

pytestmark = pytest.mark.integration


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


class TestNotificationsBridge:

    def test_degraded_event_creates_notification(self, client, monkeypatch):
        from app.core import settings as settings_module
        from app.db import database as db_module

        import asyncio
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
        from app.db.database import Base

        engine_url = "sqlite+aiosqlite:///:memory:"
        test_engine = create_async_engine(engine_url, poolclass=None)

        # SQLite :memory: por engine não compartilha conexão entre sessões —
        # usar StaticPool pra o handler e o teste enxergarem o mesmo banco.
        from sqlalchemy.pool import StaticPool
        test_engine = create_async_engine(engine_url, connect_args={"check_same_thread": False},
                                          poolclass=StaticPool)

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
            from app.services.notifications import NotificationService
            async with Session() as session:
                return await NotificationService.list(session)
        results = asyncio.run(_check())
        assert len(results) == 1
        assert "fake" in results[0].title
        assert results[0].level == "error"

        asyncio.run(test_engine.dispose())

    def test_dedup_does_not_create_second_notification_within_window(self, monkeypatch):
        import asyncio
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
        from sqlalchemy.pool import StaticPool
        from app.db.database import Base
        from app.db import database as db_module

        test_engine = create_async_engine("sqlite+aiosqlite:///:memory:",
                                          connect_args={"check_same_thread": False}, poolclass=StaticPool)

        async def _prep():
            async with test_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        asyncio.run(_prep())

        Session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
        monkeypatch.setattr(db_module, "AsyncSessionLocal", Session)

        from app.observability.events import Event
        from app.observability.notifications_bridge import _handle_critical_event

        event = Event(type="runtime.degraded", payload={"component": "fake2", "pid": 1, "detail": "x"})
        _handle_critical_event(event)
        _handle_critical_event(event)

        async def _check():
            from app.services.notifications import NotificationService
            async with Session() as session:
                return await NotificationService.list(session)
        results = asyncio.run(_check())
        assert len(results) == 1

        asyncio.run(test_engine.dispose())

    def test_ignores_non_critical_events(self, monkeypatch):
        from app.observability.events import Event
        from app.observability.notifications_bridge import _handle_critical_event

        # não deve nem tentar tocar no banco pra um evento que nao é critico
        _handle_critical_event(Event(type="package_manager.install", payload={}))
