"""
Module Runtime — Fase 9
==========================
Consolida o ciclo de execução de módulos ativos: loader único de arquivos
de backend, Runtime State (separado do Administrative State do
ModuleRegistry), ExecutionContext oficial e envelope de resultado.
"""
from app.module_runtime.loader import ModuleLoadError, load_module_file
from app.module_runtime.state import (
    ModuleRuntimeEntry, ModuleRuntimeRegistry, RuntimeState, module_runtime_registry,
)
from app.module_runtime.lifecycle import on_activate, on_deactivate, health_check
from app.module_runtime.context import ModuleExecutionContext

__all__ = [
    "ModuleLoadError", "load_module_file",
    "ModuleRuntimeEntry", "ModuleRuntimeRegistry", "RuntimeState", "module_runtime_registry",
    "on_activate", "on_deactivate", "health_check",
    "ModuleExecutionContext",
]
