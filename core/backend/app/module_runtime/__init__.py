"""
Module Runtime — Fase 9
==========================
Consolida o ciclo de execução de módulos ativos: loader único de arquivos
de backend, Runtime State (separado do Administrative State do
ModuleRegistry), ExecutionContext oficial e envelope de resultado.
"""
from app.module_runtime.context import ModuleExecutionContext
from app.module_runtime.execution import (
    CancellationToken,
    ExecutionCancelledError,
    ModuleExecutionResult,
    ProgressPhase,
    ProgressReport,
)
from app.module_runtime.lifecycle import discard_instance, health_check, on_activate, on_deactivate
from app.module_runtime.loader import ModuleLoadError, load_module_file
from app.module_runtime.state import (
    ModuleRuntimeEntry,
    ModuleRuntimeRegistry,
    RuntimeState,
    module_runtime_registry,
)

__all__ = [
    "ModuleLoadError", "load_module_file",
    "ModuleRuntimeEntry", "ModuleRuntimeRegistry", "RuntimeState", "module_runtime_registry",
    "on_activate", "on_deactivate", "health_check", "discard_instance",
    "ModuleExecutionContext",
    "ModuleExecutionResult", "CancellationToken", "ExecutionCancelledError",
    "ProgressPhase", "ProgressReport",
]
