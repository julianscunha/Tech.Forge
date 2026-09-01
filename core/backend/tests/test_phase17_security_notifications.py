"""Fase 17 Slice 8 — Notificações só pra eventos de segurança relevantes.

security.signature_invalid, security.integrity_failure e
security.module_blocked passam a virar Notification (mesmo bridge do
EventBus da Fase 14, `_handle_critical_event`) — eventos "normais"
(package_verified, secret_created, etc.) continuam sem notificação,
pra não virar spam de operação normal.

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase17_security_notifications.py -q
"""
from __future__ import annotations

import asyncio

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db import database as db_module
from app.db.database import Base
from app.observability.events import Event
from app.observability import notifications_bridge
from app.observability.notifications_bridge import _handle_critical_event, drain_pending_notifications
from app.services.notifications import NotificationService

pytestmark = pytest.mark.integration


def _memory_session(monkeypatch):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:",
                                 connect_args={"check_same_thread": False}, poolclass=StaticPool)

    async def _prep():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    asyncio.run(_prep())

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    monkeypatch.setattr(db_module, "AsyncSessionLocal", session_factory)
    return session_factory, engine


def _list_notifications(session_factory):
    async def _check():
        async with session_factory() as session:
            return await NotificationService.list(session)
    return asyncio.run(_check())


@pytest.mark.parametrize("event_type,payload", [
    ("security.signature_invalid", {"module_id": "mod_a"}),
    ("security.integrity_failure", {"module_id": "mod_a", "status": "MODIFIED"}),
    ("security.module_blocked", {"module_id": "mod_a", "reason": "oversized package"}),
])
def test_relevant_security_events_create_notification(monkeypatch, event_type, payload):
    session_factory, engine = _memory_session(monkeypatch)
    try:
        _handle_critical_event(Event(type=event_type, payload=payload))
        results = _list_notifications(session_factory)
        assert len(results) == 1
        assert results[0].module_id == "mod_a"
        assert results[0].level in ("error", "warning")
    finally:
        asyncio.run(engine.dispose())


@pytest.mark.parametrize("event_type", [
    "security.package_verified", "security.signature_valid",
    "security.secret_created", "security.secret_rotated", "security.secret_deleted",
])
def test_normal_operation_events_do_not_notify(monkeypatch, event_type):
    session_factory, engine = _memory_session(monkeypatch)
    try:
        _handle_critical_event(Event(type=event_type, payload={"module_id": "mod_a"}))
        results = _list_notifications(session_factory)
        assert results == []
    finally:
        asyncio.run(engine.dispose())


@pytest.mark.asyncio
async def test_security_event_notifies_even_when_published_from_running_loop(monkeypatch):
    """Reproduz o bug real: install()/get_module_trust() são `async def` —
    o evento é publicado DENTRO de um loop já rodando (o mesmo do uvicorn
    em produção), não de um contexto sync como os testes acima simulam
    com `asyncio.run()`. O guard antigo (`asyncio.get_running_loop()` ->
    encontra um loop -> desiste silenciosamente) nunca notificava nada
    em produção — só "funcionava" nos testes porque eles chamam de fora
    de qualquer loop."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:",
                                 connect_args={"check_same_thread": False}, poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    monkeypatch.setattr(db_module, "AsyncSessionLocal", session_factory)

    try:
        _handle_critical_event(Event(type="security.module_blocked",
                                     payload={"module_id": "mod_a", "reason": "oversized"}))
        # `_handle_critical_event` agenda a criação via create_task quando já
        # há um loop rodando — esperar a task de verdade (drain), não um sleep
        # arbitrário. Um sleep fixo é uma corrida: se a task demorar mais que
        # o valor escolhido (CI sob carga, disco lento), o teste segue antes
        # dela terminar e a task acaba escrevendo depois, já fora do `monkeypatch`
        # (achado real: um sleep de 50ms aqui já vazou uma notificação
        # "Segurança — mod_a: Instalação bloqueada..." pra dentro do banco de
        # produção usado por outros arquivos de teste, poluindo
        # test_phase2_notifications.py de forma intermitente).
        await drain_pending_notifications()

        async with session_factory() as session:
            results = await NotificationService.list(session)
        assert len(results) == 1
        assert results[0].module_id == "mod_a"
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_drain_waits_for_slow_notification_task(monkeypatch):
    """Prova que drain_pending_notifications() espera a task terminar de
    verdade, mesmo se ela demorar mais que qualquer sleep fixo razoável —
    ao contrário do `asyncio.sleep(0.05)` que este teste substituiu."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:",
                                 connect_args={"check_same_thread": False}, poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    monkeypatch.setattr(db_module, "AsyncSessionLocal", session_factory)

    real_create = notifications_bridge._create_notification

    async def _slow_create(event):
        await asyncio.sleep(0.2)  # bem mais que qualquer sleep fixo que já foi usado aqui
        await real_create(event)

    monkeypatch.setattr(notifications_bridge, "_create_notification", _slow_create)

    try:
        _handle_critical_event(Event(type="security.module_blocked",
                                     payload={"module_id": "mod_slow", "reason": "oversized"}))
        await drain_pending_notifications()

        async with session_factory() as session:
            results = await NotificationService.list(session)
        assert len(results) == 1
        assert results[0].module_id == "mod_slow"
    finally:
        await engine.dispose()
