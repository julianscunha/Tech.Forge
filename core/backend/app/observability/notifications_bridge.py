"""EventBus → Notifications — Fase 14 §31, Fase 17 §38/§39.

Só eventos críticos viram notificação — "não notificar cada log".
`runtime.degraded` (Fase 14) e 3 eventos de segurança relevantes (Fase
17): `security.signature_invalid`, `security.integrity_failure`,
`security.module_blocked` — operação normal (package_verified,
signature_valid, secret_created/rotated/deleted) não notifica, senão
vira spam. Dedup: não repete a mesma notificação (mesmo título) dentro
de uma janela de tempo — evita spam se o problema ficar oscilando.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

from app.observability.events import Event, event_bus

logger = logging.getLogger("techforge.notifications_bridge")

_DEDUP_WINDOW_MINUTES = 15

# Fase 17 — tasks de notificação agendadas via `loop.create_task()` (evento
# publicado de dentro de um handler `async def`). Guardadas aqui pra evitar
# coleta de lixo prematura e pra que `drain_pending_notifications()` possa
# esperar por elas no shutdown — sem isso, um teste (TestClient com loop
# de vida curta) pode fechar o loop antes da task terminar, vazando erro
# "Event loop is closed" pra outro teste qualquer.
_pending_tasks: set[asyncio.Task] = set()


async def drain_pending_notifications() -> None:
    """Espera todas as notificações de segurança agendadas terminarem.
    Chamado no shutdown do app (produção) e no fim de cada teste que
    dispara eventos críticos dentro de um loop já rodando."""
    if _pending_tasks:
        await asyncio.gather(*_pending_tasks, return_exceptions=True)

_SECURITY_EVENT_MESSAGES = {
    "security.signature_invalid": "Assinatura inválida — o conteúdo do módulo não confere com o publisher declarado.",
    "security.integrity_failure": "Integridade comprometida — arquivos do módulo foram alterados desde a instalação.",
    "security.module_blocked": "Instalação bloqueada por exceder limites de segurança.",
}


def _handle_critical_event(event: Event) -> None:
    if event.type not in ("runtime.degraded", *_SECURITY_EVENT_MESSAGES):
        return

    async def _safe_create() -> None:
        try:
            await _create_notification(event)
        except Exception:
            logger.exception("Failed to create notification for critical event %s", event.type)

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None:
        # Fase 17: a maioria dos call-sites de segurança publica DENTRO de
        # um handler `async def` (o mesmo loop do uvicorn) — agendar a
        # criação da notificação nesse loop em vez de desistir. Descartar
        # silenciosamente aqui significava que nenhuma notificação de
        # segurança jamais era criada em produção (só "funcionava" em
        # testes que chamam de fora de qualquer loop, via asyncio.run()).
        task = loop.create_task(_safe_create())
        _pending_tasks.add(task)
        task.add_done_callback(_pending_tasks.discard)
    else:
        try:
            asyncio.run(_safe_create())
        except Exception:
            logger.exception("Failed to create notification for critical event %s", event.type)


async def _create_notification(event: Event) -> None:
    from sqlalchemy import select

    from app.db.database import AsyncSessionLocal
    from app.models.notifications import Notification
    from app.services.notifications import NotificationService

    if event.type == "runtime.degraded":
        title = f"Componente '{event.payload.get('component')}' parou de responder"
        message = event.payload.get("detail")
        module_id = None
    else:
        module_id = event.payload.get("module_id")
        title = f"Segurança — {module_id}: {_SECURITY_EVENT_MESSAGES[event.type]}"
        message = _SECURITY_EVENT_MESSAGES[event.type]

    async with AsyncSessionLocal() as db:
        cutoff = datetime.utcnow() - timedelta(minutes=_DEDUP_WINDOW_MINUTES)
        stmt = select(Notification).where(Notification.title == title, Notification.created_at >= cutoff)
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing is not None:
            return  # dedup — já notificado recentemente

        await NotificationService.create(
            db, level="error", title=title, message=message, module_id=module_id,
        )


def wire_notifications() -> None:
    """Chamar uma vez, no import do app — assina o EventBus global."""
    event_bus.subscribe(_handle_critical_event)
