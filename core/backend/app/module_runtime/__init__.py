"""
Module Runtime — Fase 9
==========================
Consolida o ciclo de execução de módulos ativos: loader único de arquivos
de backend, Runtime State (separado do Administrative State do
ModuleRegistry), ExecutionContext oficial e envelope de resultado.
"""
from app.module_runtime.loader import ModuleLoadError, load_module_file

__all__ = ["ModuleLoadError", "load_module_file"]
