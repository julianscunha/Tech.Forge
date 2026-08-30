"""
Invocação de capacidades públicas — Fase 8 §12/§13/§14/§15
=============================================================
Chamada direta de função Python (decisão do plano): importa dinamicamente
o `backend/main.py` do módulo de serviço (mesmo mecanismo do plugin_loader)
e chama a função do export pelo nome — sem round-trip HTTP interno.

Fluxo (§13): Resolve Service → Validate Contract → Invoke → Return Result.
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid

from app.core.settings import settings
from app.module_runtime.loader import ModuleLoadError, load_module_file
from app.observability.context import bind_log_context
from app.observability.metrics import metric_emitter
from app.service_registry.descriptor import ServiceStatus
from app.service_registry.errors import (
    CapabilityNotFoundError,
    ContractViolationError,
    InvalidArgumentsError,
    ServiceDisabledError,
    ServiceExecutionFailedError,
    ServiceNotFoundError,
    ServiceUnavailableError,
)
from app.service_registry.registry import service_registry

logger = logging.getLogger("techforge.service_registry.invoker")

_BASIC_TYPES = {
    "str": str, "string": str, "int": int, "integer": int,
    "float": (int, float), "number": (int, float), "bool": bool, "boolean": bool,
    "list": list, "dict": dict,
}


def _load_export_callable(module_id: str, export_name: str):
    """
    Resolve a função do export: primeiro como função de nível de módulo
    (padrão hello_world.ping), senão como método da instância `module`
    (padrão ModuleContract, ex: veeam_m365 calculate_storage).
    """
    backend_path = settings.MODULES_INSTALLED_PATH / module_id / "backend" / "main.py"
    try:
        mod = load_module_file(f"service_registry_{module_id}", backend_path)
    except ModuleLoadError:
        return None

    if hasattr(mod, export_name):
        return getattr(mod, export_name)
    provider = getattr(mod, "module", None)
    if provider is not None and hasattr(provider, export_name):
        return getattr(provider, export_name)
    return None


def _validate_arguments(export, kwargs: dict) -> None:
    """§14 — argumentos obrigatórios presentes, tipos básicos, sem desconhecidos."""
    known = {p.get("name") for p in export.parameters}
    unknown = sorted(set(kwargs) - known)
    if unknown:
        raise InvalidArgumentsError(
            f"Unknown argument(s) for '{export.name}': {unknown}"
        )

    for p in export.parameters:
        name = p.get("name")
        if p.get("required") and name not in kwargs:
            raise InvalidArgumentsError(
                f"Missing required argument '{name}' for '{export.name}'"
            )
        if name in kwargs:
            expected = _BASIC_TYPES.get(str(p.get("type", "")).lower())
            if expected and not isinstance(kwargs[name], expected):
                raise InvalidArgumentsError(
                    f"Argument '{name}' for '{export.name}' must be of type "
                    f"{p.get('type')}, got {type(kwargs[name]).__name__}"
                )


def invoke(service_id: str, export_name: str, **kwargs):
    """
    Invoca uma capacidade pública de um Service Module.

    Raises:
        ServiceNotFoundError, ServiceDisabledError, ServiceUnavailableError,
        CapabilityNotFoundError, ContractViolationError, InvalidArgumentsError,
        ServiceExecutionFailedError
    """
    descriptor = service_registry.find_service(service_id)
    if descriptor is None:
        raise ServiceNotFoundError(service_id)
    if descriptor.status == ServiceStatus.DISABLED:
        raise ServiceDisabledError(service_id)
    if descriptor.status != ServiceStatus.ACTIVE:
        raise ServiceUnavailableError(service_id)
    if descriptor.contract is None:
        raise ContractViolationError(f"Service '{service_id}' has no published contract")

    export = next((e for e in descriptor.contract.exports if e.name == export_name), None)
    if export is None:
        raise CapabilityNotFoundError(f"{service_id}.{export_name}")

    _validate_arguments(export, kwargs)

    func = _load_export_callable(descriptor.module_id, export_name)
    if func is None:
        raise ContractViolationError(
            f"Export '{export_name}' declared in contract but not found in "
            f"{descriptor.module_id}/backend/main.py"
        )

    metric_emitter.counter("module_executions").inc()
    execution_id = str(uuid.uuid4())
    start = time.monotonic()
    with bind_log_context(module_id=descriptor.module_id, execution_id=execution_id):
        try:
            result = func(**kwargs)
            if asyncio.iscoroutine(result):
                result = asyncio.run(result)
            duration = time.monotonic() - start
            metric_emitter.histogram("execution_duration").observe(duration)
            _persist_execution_history(execution_id, descriptor.module_id, "SUCCESS", duration)
            return result
        except Exception as exc:
            duration = time.monotonic() - start
            metric_emitter.counter("execution_failures").inc()
            metric_emitter.histogram("execution_duration").observe(duration)
            _persist_execution_history(execution_id, descriptor.module_id, "FAILED", duration, str(exc))
            # §15 — não expor stack trace interno de outro módulo ao chamador;
            # o detalhe fica só no log do Core.
            logger.warning("Execution of %s.%s failed: %s", service_id, export_name, exc)
            raise ServiceExecutionFailedError(
                f"Execution of '{service_id}.{export_name}' failed"
            ) from None


def _persist_execution_history(execution_id: str, module_id: str, status: str,
                                duration_seconds: float, error_summary: str | None = None) -> None:
    """Grava no Execution History (Fase 14 §23). Observability nunca pode
    quebrar a execução real do módulo (spec §37) — se já estamos dentro de
    um event loop rodando, não dá pra usar asyncio.run() aqui; a
    persistência é pulada silenciosamente (logada em debug) em vez de
    lançar."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        pass
    else:
        logger.debug("Skipping execution history persistence: already inside a running event loop")
        return

    async def _write() -> None:
        from app.db.database import AsyncSessionLocal
        from app.services.execution_history import ExecutionHistoryService
        async with AsyncSessionLocal() as db:
            await ExecutionHistoryService.record(
                db, execution_id=execution_id, module_id=module_id, status=status,
                duration_seconds=duration_seconds, error_summary=error_summary,
            )

    try:
        asyncio.run(_write())
    except Exception:
        logger.exception("Failed to persist execution history for %s", execution_id)
