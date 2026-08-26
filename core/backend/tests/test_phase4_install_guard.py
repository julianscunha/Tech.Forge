"""Fase 4 — Guard de instalação: mesmo ID em estado inválido ou já existente.

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase4_install_guard.py -q
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))

sys.path.insert(0, str(Path(__file__).parent))
from test_phase4 import make_package_manager, make_mod_file, MANIFEST_BASE
from app.package_manager.enums import InstallStatus


def test_rejects_id_already_registered_invalid(tmp_path):
    """ID presente no registry com status INVALID → instalação rejeitada."""
    from app.module_engine.registry import registry
    from app.module_engine.enums import ModuleStatus
    from datetime import datetime

    registry.register(_entry("blocked_mod", ModuleStatus.INVALID))
    try:
        pm = make_package_manager(tmp_path)
        mod = make_mod_file(tmp_path, {**MANIFEST_BASE, "id": "blocked_mod"})
        result = asyncio_run(pm.install(mod))
        assert result.status == InstallStatus.FAILED
        assert "invalid" in result.message.lower()
        # nada foi instalado no disco
        assert not (tmp_path / "installed" / "blocked_mod").exists()
    finally:
        registry.deregister("blocked_mod")


def test_rejects_id_already_registered_incompatible(tmp_path):
    """ID presente no registry com status INCOMPATIBLE → instalação rejeitada."""
    from app.module_engine.registry import registry
    from app.module_engine.enums import ModuleStatus

    registry.register(_entry("incompat_mod", ModuleStatus.INCOMPATIBLE))
    try:
        pm = make_package_manager(tmp_path)
        mod = make_mod_file(tmp_path, {**MANIFEST_BASE, "id": "incompat_mod"})
        result = asyncio_run(pm.install(mod))
        assert result.status == InstallStatus.FAILED
        # nada foi instalado no disco
        assert not (tmp_path / "installed" / "incompat_mod").exists()
    finally:
        registry.deregister("incompat_mod")


def test_allows_fresh_id(tmp_path):
    """ID novo instala normalmente (guard não bloqueia demais)."""
    pm = make_package_manager(tmp_path)
    mod = make_mod_file(tmp_path, MANIFEST_BASE.copy())
    result = asyncio_run(pm.install(mod))
    assert result.status == InstallStatus.SUCCESS


def _entry(module_id, status):
    from app.module_engine.registry import ModuleEntry
    return ModuleEntry(
        module_id=module_id, name=module_id.title(), version="0.1.0",
        category="Test", vendor="V", author="A", description="D",
        status=status, install_date=datetime.now(),
    )


def asyncio_run(coro):
    import asyncio
    return asyncio.run(coro)
