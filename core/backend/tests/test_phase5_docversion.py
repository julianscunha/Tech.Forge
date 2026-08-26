"""Fase 5 Slice 3 — Versionamento documental (spec §17).

Manifest pode declarar bloco opcional `documentation:` com version/applies_to.
O parser expõe esses metadados; sem resolvedor de versão (spec veda).

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase5_docversion.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))

from app.module_engine.manifest import ManifestParser


BASE_MANIFEST = {
    "id": "ver_mod", "name": "Ver Mod", "version": "1.0.0",
    "description": "d", "category": "Test", "vendor": "V", "author": "A",
    "entry_backend": "backend/main.py", "entry_frontend": "frontend/index.tsx",
    "icon": "box", "order": 1,
}


def _write_module(tmp_path: Path, extra: dict) -> Path:
    mod = tmp_path / "ver_mod"
    (mod / "backend").mkdir(parents=True)
    (mod / "frontend").mkdir()
    (mod / "backend" / "main.py").write_text("", encoding="utf-8")
    (mod / "frontend" / "index.tsx").write_text("", encoding="utf-8")
    data = {**BASE_MANIFEST, **extra}
    (mod / "manifest.yaml").write_text(yaml.dump(data), encoding="utf-8")
    return mod


def test_documentation_block_parsed(tmp_path):
    mod = _write_module(tmp_path, {
        "documentation": {
            "version": "1.1.0",
            "applies_to": {"techforge": ">=1.0.0,<2.0.0"},
        },
    })
    parsed = ManifestParser.parse(mod)
    assert parsed.documentation_version == "1.1.0"
    assert parsed.documentation_applies_to == {"techforge": ">=1.0.0,<2.0.0"}


def test_documentation_absent_defaults(tmp_path):
    mod = _write_module(tmp_path, {})
    parsed = ManifestParser.parse(mod)
    assert parsed.documentation_version is None
    assert parsed.documentation_applies_to in (None, {})


def test_documentation_invalid_type_rejected(tmp_path):
    """documentation.version não-semver deve ser rejeitado (§17)."""
    mod = _write_module(tmp_path, {
        "documentation": {"version": "not-a-version"},
    })
    with pytest.raises(Exception):
        ManifestParser.parse(mod)
