"""
Runtime Integrity Verification — Fase 10 §15/§16/§20
=========================================================
Reverifica a integridade de um módulo já instalado sob demanda —
startup, update, verificação manual (§28: nunca polling contínuo).
Notifica (dedupe) quando detecta qualquer estado diferente de VALID;
nunca bloqueia execução por padrão (§16 — política inicial não impede
automaticamente, só avisa).
"""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.models.notifications import Notification
from app.module_trust.integrity import IntegrityResult, IntegrityStatus, verify_integrity
from app.services.notifications import NotificationService


async def verify_module_integrity(module_id: str, db: AsyncSession) -> IntegrityResult:
    """Reverifica um módulo já instalado. Notifica (dedupe) se o
    resultado não for VALID. Nunca bloqueia execução — só reporta."""
    package_dir = settings.MODULES_INSTALLED_PATH / module_id
    result = verify_integrity(package_dir)

    if result.status != IntegrityStatus.VALID:
        await _notify_integrity_issue(db, module_id, result)

    return result


async def _notify_integrity_issue(db: AsyncSession, module_id: str,
                                  result: IntegrityResult) -> None:
    title = "Module integrity changed"
    parts = [result.status.value]
    if result.detail:
        parts.append(result.detail)
    if result.modified_files:
        parts.append(f"modified={result.modified_files}")
    if result.missing_files:
        parts.append(f"missing={result.missing_files}")
    if result.unexpected_files:
        parts.append(f"unexpected={result.unexpected_files}")
    message = f"{module_id}: {' | '.join(parts)}"

    existing = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.title == title, Notification.message == message))
    if existing.scalar() == 0:
        await NotificationService.create(
            db, level="warning", title=title, message=message, module_id=module_id)
