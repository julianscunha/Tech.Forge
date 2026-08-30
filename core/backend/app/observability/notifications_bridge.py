"""EventBus → Notifications — Fase 14 §31.

Só eventos críticos viram notificação — "não notificar cada log". Hoje
o único evento crítico real que o EventBus carrega é `runtime.degraded`
(componente de runtime parou de responder). Dedup: não repete a mesma
notificação (mesmo título) dentro de uma janela de tempo — evita spam se
o componente ficar oscilando.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

from app.observability.events import Event, event_bus

logger = logging.getLogger("techforge.notifications_bridge")

_DEDUP_WINDOW_MINUTES = 15


def _handle_critical_event(event: Event) -> None:
    if event.type != "runtime.degraded":
        return

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        pass
    else:
        logger.debug("Skipping notification: already inside a running event loop")
        return

    try:
        asyncio.run(_create_notification(event))
    except Exception:
        logger.exception("Failed to create notification for critical event %s", event.type)


async def _create_notification(event: Event) -> None:
    from sqlalchemy import select

    from app.db.database import AsyncSessionLocal
    from app.models.notifications import Notification
    from app.services.notifications import NotificationService

    title = f"Componente '{event.payload.get('component')}' parou de responder"
    async with AsyncSessionLocal() as db:
        cutoff = datetime.utcnow() - timedelta(minutes=_DEDUP_WINDOW_MINUTES)
        stmt = select(Notification).where(Notification.title == title, Notification.created_at >= cutoff)
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing is not None:
            return  # dedup — já notificado recentemente

        await NotificationService.create(
            db, level="error", title=title, message=event.payload.get("detail"),
        )


def wire_notifications() -> None:
    """Chamar uma vez, no import do app — assina o EventBus global."""
    event_bus.subscribe(_handle_critical_event)
