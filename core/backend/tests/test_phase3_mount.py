"""Fase 3 quality — idempotência do mount_module_routers (R1).

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase3_mount.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))

from fastapi import FastAPI

from app.module_engine.plugin_loader import mount_module_routers


def test_double_mount_does_not_duplicate_routes():
    """Chamar mount 2× não deve duplicar rotas de módulos já montados."""
    from app.main import app

    routes_before = len(app.routes)
    result = mount_module_routers(app)
    routes_after = len(app.routes)
    # nenhum módulo novo a montar (todos já foram montados no startup/lifespan)
    assert result.mounted == []
    assert routes_after == routes_before


def test_mount_result_tracks_state():
    from app.module_engine.plugin_loader import _mounted_module_ids
    assert isinstance(_mounted_module_ids, set)
