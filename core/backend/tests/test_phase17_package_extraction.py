"""Fase 17 Slice 1 — install()/update() bloqueiam pacote oversized de verdade
(não só a função isolada `safe_extract`, spec §16/§18).

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase17_package_extraction.py -q
"""
from __future__ import annotations

import asyncio
import zipfile
from pathlib import Path

import pytest
import yaml

from app.package_manager.enums import InstallStatus
from tests.test_phase4 import MANIFEST_BASE, make_mod_file, make_package_manager

pytestmark = pytest.mark.integration


def _make_oversized_mod(tmp: Path, module_id: str) -> Path:
    """.mod pequeno no disco (zip bem comprimido), mas descomprimido excede
    qualquer limite razoável — o zip bomb clássico."""
    manifest = {**MANIFEST_BASE, "id": module_id}
    mod_path = tmp / f"{module_id}-1.0.0.mod"
    with zipfile.ZipFile(mod_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.yaml", yaml.dump(manifest))
        zf.writestr("backend/main.py", "x = 1\n")
        zf.writestr("frontend/index.tsx", "export default function(){}\n")
        # Altamente compressível: poucos KB no zip, ~50MB descomprimido.
        zf.writestr("backend/bomb.bin", b"0" * 50_000_000)
    return mod_path


def test_install_blocks_oversized_package(tmp_path, monkeypatch):
    from app.core.settings import settings
    monkeypatch.setattr(settings, "MAX_PACKAGE_UNCOMPRESSED_SIZE", 1_000_000)

    pm = make_package_manager(tmp_path)
    mod_path = _make_oversized_mod(tmp_path, "zipbomb_mod")

    result = asyncio.run(pm.install(mod_path))

    assert result.status == InstallStatus.FAILED
    assert not (pm._installed / "zipbomb_mod").exists()


def test_install_within_limits_still_works(tmp_path, monkeypatch):
    from app.core.settings import settings
    monkeypatch.setattr(settings, "MAX_PACKAGE_UNCOMPRESSED_SIZE", 200_000_000)
    monkeypatch.setattr(settings, "MAX_PACKAGE_FILE_COUNT", 5_000)

    pm = make_package_manager(tmp_path)
    mod_path = make_mod_file(tmp_path, {**MANIFEST_BASE, "id": "normal_mod"})

    result = asyncio.run(pm.install(mod_path))

    assert result.status == InstallStatus.SUCCESS
    assert (pm._installed / "normal_mod").is_dir()
