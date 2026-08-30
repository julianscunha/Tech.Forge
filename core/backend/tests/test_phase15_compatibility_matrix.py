"""Fase 15 Slice 5 — compatibility matrix tests (spec §21).

Duas frentes:
  - Core Version × Module Version (`app.package_manager.compatibility`) —
    corrigido aqui para usar `packaging.version.Version` (já dependência,
    Fase 12) em vez do parser ingênuo anterior, que quebrava silenciosamente
    em versões pre-release (usadas pelos canais de pre-release, Slice 12).
  - Module × Dependency Version — já coberto em
    `test_phase8_1_dependency_governance.py` via `packaging`
    (`Dependency.satisfies_version`); não duplicado aqui.

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase15_compatibility_matrix.py -q
"""
from __future__ import annotations

import pytest

from app.package_manager.compatibility import check_compatibility
from app.package_manager.enums import CompatibilityLevel

pytestmark = pytest.mark.unit


def test_platform_prerelease_version_within_range_is_compatible():
    """Regressão: '1.5.0-rc.1' quebrava o parser ingênuo (split('.') gera um
    componente '0-rc' que não converte pra int, caindo em (0,0,0) e sendo
    julgado INCOMPATIBLE mesmo dentro do range declarado)."""
    result = check_compatibility(
        platform_version="1.5.0-rc.1", min_version="1.0.0", max_version="2.0.0"
    )
    assert result == CompatibilityLevel.COMPATIBLE


def test_module_prerelease_min_version_is_respected():
    result = check_compatibility(
        platform_version="1.6.0", min_version="1.5.0-rc.1", max_version="2.0.0"
    )
    assert result == CompatibilityLevel.COMPATIBLE


def test_platform_version_outside_range_is_incompatible():
    result = check_compatibility(platform_version="3.0.0", min_version="1.0.0", max_version="2.0.0")
    assert result == CompatibilityLevel.INCOMPATIBLE


def test_platform_version_near_max_boundary_is_warning():
    result = check_compatibility(platform_version="2.0.0", min_version="1.0.0", max_version="2.1.0")
    assert result == CompatibilityLevel.WARNING


def test_malformed_version_string_does_not_raise():
    """Manifests malformados já são bloqueados na validação (Fase 1) — aqui
    só garantimos que o compatibility checker não propaga exceção não-tratada
    caso algo passe por trás dela."""
    result = check_compatibility(platform_version="not-a-version", min_version="1.0.0", max_version="2.0.0")
    assert result in (CompatibilityLevel.COMPATIBLE, CompatibilityLevel.WARNING, CompatibilityLevel.INCOMPATIBLE)
