"""Fase 15 Slice 11 — Build artifacts & integrity (spec §28/§41).

Módulo (.mod) já tem checksum + version desde a Fase 4/5 (`BuildResult`,
`PackageBuilder`) — aqui: (1) adiciona `built_at` pra completar "version +
checksum + build metadata" (§41); (2) fecha uma segunda fonte de verdade de
versão que existia solta em `core/frontend/package.json` (§24).

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase15_build_artifacts.py -q
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.core.settings import settings
from app.package_manager.builder import PackageBuilder

pytestmark = pytest.mark.unit


def test_frontend_package_json_version_matches_platform_version():
    """Regressão: package.json tinha "version": "1.0.0" independente de
    PLATFORM_VERSION — duas fontes de verdade que já podiam divergir
    silenciosamente (spec §24)."""
    package_json = settings.BASE_DIR / "core" / "frontend" / "package.json"
    data = json.loads(package_json.read_text(encoding="utf-8"))
    assert data["version"] == settings.PLATFORM_VERSION


def test_build_result_includes_built_at_timestamp(tmp_path):
    module_dir = tmp_path / "sample_mod"
    (module_dir / "backend").mkdir(parents=True)
    (module_dir / "frontend").mkdir(parents=True)
    (module_dir / "manifest.yaml").write_text(
        "id: sample_mod\nname: Sample\nversion: 1.0.0\ncategory: C\nvendor: V\nauthor: A\ndescription: D\n",
        encoding="utf-8",
    )
    result = PackageBuilder.build(module_dir, output_dir=tmp_path)
    assert result.built_at
    # ISO 8601 básico — não valida timezone/precisão, só a forma geral.
    assert "T" in result.built_at
