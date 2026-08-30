"""Fase 12 Slice 3 (parte 1) — manifest `configuration.fields` (spec §10).

Manifest pode declarar bloco opcional `configuration: fields: [...]` com
id/type/default por campo. Tipado e validável no parse — falha cedo, não
só na hora de usar.

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase12_manifest_config.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))

import pytest

from app.module_engine.manifest import ManifestError, ManifestParser

pytestmark = pytest.mark.unit


BASE_MANIFEST = {
    "id": "cfg_mod", "name": "Cfg Mod", "version": "1.0.0",
    "description": "d", "category": "Test", "vendor": "V", "author": "A",
    "entry_backend": "backend/main.py", "entry_frontend": "frontend/index.tsx",
    "icon": "box", "order": 1,
}


def _write_module(tmp_path: Path, extra: dict) -> Path:
    mod = tmp_path / "cfg_mod"
    (mod / "backend").mkdir(parents=True)
    (mod / "frontend").mkdir()
    (mod / "backend" / "main.py").write_text("", encoding="utf-8")
    (mod / "frontend" / "index.tsx").write_text("", encoding="utf-8")
    data = {**BASE_MANIFEST, **extra}
    (mod / "manifest.yaml").write_text(yaml.dump(data), encoding="utf-8")
    return mod


def test_configuration_fields_parsed(tmp_path):
    mod = _write_module(tmp_path, {
        "configuration": {"fields": [
            {"id": "retention_days", "type": "integer", "default": 30},
            {"id": "enabled", "type": "boolean", "default": True},
        ]},
    })
    parsed = ManifestParser.parse(mod)
    assert [f.id for f in parsed.configuration_fields] == ["retention_days", "enabled"]
    assert parsed.configuration_fields[0].type == "integer"
    assert parsed.configuration_fields[0].default == 30


def test_configuration_absent_defaults_to_empty_list(tmp_path):
    mod = _write_module(tmp_path, {})
    parsed = ManifestParser.parse(mod)
    assert parsed.configuration_fields == []


def test_configuration_field_missing_type_rejected(tmp_path):
    mod = _write_module(tmp_path, {
        "configuration": {"fields": [{"id": "x"}]},
    })
    with pytest.raises(ManifestError):
        ManifestParser.parse(mod)


def test_configuration_field_unknown_type_rejected(tmp_path):
    mod = _write_module(tmp_path, {
        "configuration": {"fields": [{"id": "x", "type": "not_a_type"}]},
    })
    with pytest.raises(ManifestError):
        ManifestParser.parse(mod)


def test_configuration_duplicate_field_id_rejected(tmp_path):
    mod = _write_module(tmp_path, {
        "configuration": {"fields": [
            {"id": "x", "type": "string"},
            {"id": "x", "type": "integer"},
        ]},
    })
    with pytest.raises(ManifestError):
        ManifestParser.parse(mod)
