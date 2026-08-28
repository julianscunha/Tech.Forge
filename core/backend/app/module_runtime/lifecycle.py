"""
Lifecycle hooks reais — Fase 9 §10/§18 Slice 3
==================================================
Conecta de verdade os hooks do ModuleContract (`enable`/`disable`/
`health_check`) que antes eram declarados no SDK mas nunca chamados por
nada do Core (só `uninstall()` já era invocado, desde a Fase 4). Um hook
que falha é best-effort: nunca bloqueia a transição administrativa em si
(Error Boundary backend — §15) — só marca o Runtime State como FAILED/
DEGRADED com o erro registrado.
"""
from __future__ import annotations

import asyncio
import logging

from app.core.settings import settings
from app.module_runtime.loader import ModuleLoadError, load_module_file
from app.module_runtime.state import RuntimeState, module_runtime_registry

logger = logging.getLogger("techforge.module_runtime.lifecycle")

# A instância `module` de um ModuleContract representa a execução de UM
# módulo ativo — precisa persistir entre enable()/health_check()/disable()
# (ex: um contador interno, uma conexão aberta em enable()). Diferente do
# invoker.py da Fase 8 (invocação de capability é stateless por natureza),
# aqui cacheamos por module_id em vez de recarregar o arquivo a cada chamada.
_instances: dict[str, object] = {}


def _load_module_instance(module_id: str, entry_backend: str):
    if module_id in _instances:
        return _instances[module_id]

    backend_path = settings.MODULES_INSTALLED_PATH / module_id / entry_backend
    try:
        py_module = load_module_file(f"techforge_modules.{module_id}.runtime_hook", backend_path)
    except ModuleLoadError:
        return None

    instance = getattr(py_module, "module", None)
    if instance is not None:
        _instances[module_id] = instance
    return instance


def discard_instance(module_id: str) -> None:
    """Chamado quando o módulo é removido/desinstalado — não deve sobreviver
    à remoção física dos arquivos."""
    _instances.pop(module_id, None)


async def on_activate(module_id: str, entry_backend: str) -> None:
    """Chama enable() best-effort depois que a ativação administrativa já
    validou dependências (Fase 8.1) e mudou o status pra INSTALLED."""
    instance = _load_module_instance(module_id, entry_backend)
    enable = getattr(instance, "enable", None)
    if not callable(enable):
        module_runtime_registry.set_state(module_id, RuntimeState.READY)
        return

    try:
        result = enable()
        if asyncio.iscoroutine(result):
            await result
        module_runtime_registry.set_state(module_id, RuntimeState.READY)
    except Exception as exc:
        logger.warning("enable() hook failed for %s: %s", module_id, exc)
        module_runtime_registry.set_state(module_id, RuntimeState.FAILED, last_error=str(exc))


async def on_deactivate(module_id: str, entry_backend: str) -> None:
    """Chama disable() best-effort depois que a desativação administrativa
    já validou dependentes (Fase 8.1)."""
    instance = _load_module_instance(module_id, entry_backend)
    disable = getattr(instance, "disable", None)
    if callable(disable):
        try:
            result = disable()
            if asyncio.iscoroutine(result):
                await result
        except Exception as exc:
            logger.warning("disable() hook failed for %s: %s", module_id, exc)

    module_runtime_registry.set_state(module_id, RuntimeState.STOPPED)


async def health_check(module_id: str, entry_backend: str) -> RuntimeState:
    """§18 — sob demanda, sem cache. Mapeia HealthResult -> RuntimeState."""
    instance = _load_module_instance(module_id, entry_backend)
    check = getattr(instance, "health_check", None)
    if not callable(check):
        return module_runtime_registry.set_state(module_id, RuntimeState.READY).state

    try:
        result = check()
        if asyncio.iscoroutine(result):
            result = await result
        if getattr(result, "is_healthy", True):
            entry = module_runtime_registry.set_state(module_id, RuntimeState.READY)
        else:
            entry = module_runtime_registry.set_state(
                module_id, RuntimeState.DEGRADED, last_error=getattr(result, "message", None))
        return entry.state
    except Exception as exc:
        logger.warning("health_check() hook failed for %s: %s", module_id, exc)
        entry = module_runtime_registry.set_state(module_id, RuntimeState.FAILED, last_error=str(exc))
        return entry.state
