"""Fase 15 Slice 12 — Pre-release channels (spec §35) e SemVer com pre-release.

Mecanismo apenas — sem UI de catálogo dedicada (decisão do plano: sem
usuários externos ainda pra segmentar canal visualmente).

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase15_prerelease_channels.py -q
"""
from __future__ import annotations

import yaml

import pytest

from app.module_engine.manifest import ManifestError, ManifestParser

pytestmark = pytest.mark.unit

BASE_MANIFEST = {
    "id": "chan_mod",
    "name": "Channel Module",
    "version": "1.0.0",
    "category": "Utilities",
    "vendor": "TechForge",
    "author": "TechForge",
    "description": "D",
    "entry_backend": "backend/main.py",
    "entry_frontend": "frontend/main.js",
    "icon": "boxes",
    "order": 1,
}


def _write_manifest(tmp_path, overrides=None):
    mod_dir = tmp_path / "chan_mod"
    (mod_dir / "backend").mkdir(parents=True)
    (mod_dir / "frontend").mkdir(parents=True)
    manifest = dict(BASE_MANIFEST)
    manifest.update(overrides or {})
    (mod_dir / "manifest.yaml").write_text(yaml.dump(manifest), encoding="utf-8")
    return mod_dir


def test_channel_defaults_to_stable_when_omitted(tmp_path):
    mod_dir = _write_manifest(tmp_path)
    parsed = ManifestParser.parse(mod_dir)
    assert parsed.channel == "stable"


def test_channel_accepts_beta(tmp_path):
    mod_dir = _write_manifest(tmp_path, {"channel": "beta"})
    parsed = ManifestParser.parse(mod_dir)
    assert parsed.channel == "beta"


def test_channel_accepts_development(tmp_path):
    mod_dir = _write_manifest(tmp_path, {"channel": "development"})
    assert ManifestParser.parse(mod_dir).channel == "development"


def test_channel_rejects_unknown_value(tmp_path):
    mod_dir = _write_manifest(tmp_path, {"channel": "nightly"})
    with pytest.raises(ManifestError, match="channel"):
        ManifestParser.parse(mod_dir)


def test_module_version_accepts_prerelease_suffix(tmp_path):
    """Regressão: version usava regex estrita (^\\d+\\.\\d+\\.\\d+$), que
    rejeitava sufixo pre-release — bloquearia qualquer módulo em canal
    beta/development declarando '1.5.0-rc.1'."""
    mod_dir = _write_manifest(tmp_path, {"version": "1.5.0-rc.1", "channel": "beta"})
    parsed = ManifestParser.parse(mod_dir)
    assert parsed.version == "1.5.0-rc.1"


def test_manifest_raw_carries_channel_for_downstream_consumers(tmp_path):
    mod_dir = _write_manifest(tmp_path, {"channel": "beta"})
    parsed = ManifestParser.parse(mod_dir)
    assert parsed.raw["channel"] == "beta"
