"""Log Context — Fase 14 §6.

Contexto propagável via contextvars: nenhum campo é obrigatório, usa o que
estiver disponível no momento do log (platform_version, module_id,
module_version, runtime_id, execution_id, request_id, deployment_mode).
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Iterator

_log_context: ContextVar[dict[str, Any]] = ContextVar("log_context", default={})


def get_log_context() -> dict[str, Any]:
    return dict(_log_context.get())


@contextmanager
def bind_log_context(**fields: Any) -> Iterator[None]:
    """Mescla `fields` no contexto atual pela duração do `with`; restaura o
    contexto anterior ao sair (mesmo em caso de exceção)."""
    previous = _log_context.get()
    token = _log_context.set({**previous, **fields})
    try:
        yield
    finally:
        _log_context.reset(token)
