"""
Loader único de arquivos de backend de módulo — Fase 9 §10 Slice 1
======================================================================
Antes desta fase, o mesmo padrão de import dinâmico
(`importlib.util.spec_from_file_location` → `exec_module`) estava
duplicado em `module_engine/plugin_loader.py`,
`service_registry/invoker.py` e `package_manager/manager.py`. Este módulo
concentra só o mecanismo de import — cada chamador continua decidindo o
que fazer com o objeto Python importado (router, export, instância
ModuleContract), que é a parte genuinamente diferente entre os três usos.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


class ModuleLoadError(Exception):
    """Raised when a module's backend entry file cannot be dynamically imported."""


def load_module_file(import_name: str, file_path: Path) -> ModuleType:
    """
    Dynamically imports a Python file as a module by explicit file path, so
    it does not need to be on sys.path and cannot collide with core
    packages or with other modules' same-named files.
    """
    if not file_path.is_file():
        raise ModuleLoadError(f"backend entry not found: {file_path}")

    spec = importlib.util.spec_from_file_location(import_name, file_path)
    if spec is None or spec.loader is None:
        raise ModuleLoadError(f"cannot create import spec for {file_path}")

    py_module = importlib.util.module_from_spec(spec)
    sys.modules[import_name] = py_module
    try:
        spec.loader.exec_module(py_module)
    except Exception as exc:
        raise ModuleLoadError(f"failed to execute {file_path}: {exc}") from exc

    return py_module
