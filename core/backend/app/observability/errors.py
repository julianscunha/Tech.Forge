"""Captura automática de erro — Fase 14 §19/§25.

Ponto único de escrita no Error Registry pros 3 lugares que capturam erro
automaticamente hoje: falha de execução (invoker), falha de dependência
(package_manager), erro de runtime (runtime.degraded). Sync e best-effort
de propósito — observability nunca pode quebrar o caminho real que está
sendo observado (spec §37): se já estamos dentro de um event loop
rodando, ou se a escrita falhar por qualquer motivo, só loga e segue.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

logger = logging.getLogger("techforge.error_registry")


def capture_error(
    source: str,
    message: str,
    *,
    module_id: Optional[str] = None,
    execution_id: Optional[str] = None,
    detail: Optional[str] = None,
) -> None:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        pass
    else:
        logger.debug("Skipping error registry persistence: already inside a running event loop")
        return

    async def _write() -> None:
        from app.db.database import AsyncSessionLocal
        from app.services.error_registry import ErrorRegistryService
        async with AsyncSessionLocal() as db:
            await ErrorRegistryService.record(
                db, source=source, message=message, detail=detail,
                module_id=module_id, execution_id=execution_id,
            )

    try:
        asyncio.run(_write())
    except Exception:
        logger.exception("Failed to persist error record (source=%s)", source)


async def capture_error_async(
    source: str,
    message: str,
    *,
    module_id: Optional[str] = None,
    execution_id: Optional[str] = None,
    detail: Optional[str] = None,
) -> None:
    """Mesma coisa que `capture_error`, pra chamadores que já estão dentro
    de uma função async (ex: PackageManager.install()) — usa `await`
    direto em vez do truque de detectar/evitar um event loop rodando."""
    try:
        from app.db.database import AsyncSessionLocal
        from app.services.error_registry import ErrorRegistryService
        async with AsyncSessionLocal() as db:
            await ErrorRegistryService.record(
                db, source=source, message=message, detail=detail,
                module_id=module_id, execution_id=execution_id,
            )
    except Exception:
        logger.exception("Failed to persist error record (source=%s)", source)
