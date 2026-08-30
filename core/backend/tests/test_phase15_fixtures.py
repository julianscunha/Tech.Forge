"""Fase 15 Slice 2 — fixtures centralizadas (spec §13).

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase15_fixtures.py -q
"""
from __future__ import annotations

import pytest
import yaml

pytestmark = pytest.mark.unit


def test_module_dir_factory_creates_installable_structure(module_dir_factory):
    mod_dir = module_dir_factory(module_id="acme_widget")

    assert (mod_dir / "backend" / "api.py").exists()
    assert (mod_dir / "frontend" / "main.js").exists()
    assert (mod_dir / "manifest.yaml").exists()

    manifest = yaml.safe_load((mod_dir / "manifest.yaml").read_text(encoding="utf-8"))
    assert manifest["id"] == "acme_widget"
    assert manifest["version"] == "1.0.0"


def test_module_dir_factory_accepts_manifest_overrides(module_dir_factory):
    mod_dir = module_dir_factory(module_id="acme_widget", manifest_overrides={"version": "2.3.1"})
    manifest = yaml.safe_load((mod_dir / "manifest.yaml").read_text(encoding="utf-8"))
    assert manifest["version"] == "2.3.1"


def test_valid_manifest_fixture_has_all_required_fields(valid_manifest):
    for field in ("id", "name", "version", "category", "vendor", "author", "description"):
        assert field in valid_manifest


def test_invalid_manifest_fixture_is_missing_a_required_field(invalid_manifest):
    required = {"id", "name", "version", "category", "vendor", "author", "description"}
    assert not required.issubset(invalid_manifest.keys())
