"""Fase 17 Slice 7 — GET /api/v1/modules/{id}/sbom (spec §31/§32).

SBOM/Supply Chain mínimo — reaproveita dependency_engine (dependências
já declaradas no manifest) + Trust/Publisher já existentes. Sem SPDX/
CycloneDX, sem lib nova, nenhuma lógica de resolução duplicada.

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase17_sbom.py -q
"""
from __future__ import annotations

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.core.settings import settings
from app.main import app
from app.module_engine.enums import ModuleStatus
from app.module_engine.registry import ModuleEntry, registry
from app.module_trust.integrity import write_integrity_manifest

pytestmark = pytest.mark.integration


def test_sbom_reflects_declared_dependencies_and_version(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "MODULES_INSTALLED_PATH", tmp_path)
    module_id = "sbom_test_mod"
    mod_dir = tmp_path / module_id
    (mod_dir / "backend").mkdir(parents=True)
    (mod_dir / "backend" / "main.py").write_text("x=1\n", encoding="utf-8")
    write_integrity_manifest(mod_dir)

    manifest_raw = {
        "id": module_id,
        "dependencies": [
            {"target": {"type": "module", "id": "other_mod"},
             "version_range": ">=1.0.0", "required": True},
            {"target": {"type": "capability", "id": "storage.kv"},
             "required": False},
        ],
    }

    with TestClient(app) as client:
        registry.register(ModuleEntry(
            module_id=module_id, name=module_id, version="2.3.1",
            category="C", vendor="V", author="A", description="D",
            status=ModuleStatus.INSTALLED, install_date=datetime.now(),
            manifest_raw=manifest_raw))

        try:
            resp = client.get(f"/api/v1/modules/{module_id}/sbom")
            assert resp.status_code == 200
            body = resp.json()
        finally:
            registry.deregister(module_id)

    assert body["module"] == module_id
    assert body["version"] == "2.3.1"
    assert len(body["dependencies"]) == 2
    module_dep = next(d for d in body["dependencies"] if d["target_id"] == "other_mod")
    assert module_dep["target_type"] == "module"
    assert module_dep["version_range"] == ">=1.0.0"
    assert module_dep["required"] is True
    capability_dep = next(d for d in body["dependencies"] if d["target_id"] == "storage.kv")
    assert capability_dep["required"] is False
    assert body["signature_status"] == "NOT_CONFIGURED"
    assert body["publisher"] is None
    assert body["checksum"] is None


def test_sbom_reflects_declared_checksum_when_present(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "MODULES_INSTALLED_PATH", tmp_path)
    module_id = "sbom_checksum_test"
    mod_dir = tmp_path / module_id
    (mod_dir / "backend").mkdir(parents=True)
    (mod_dir / "backend" / "main.py").write_text("x=1\n", encoding="utf-8")
    write_integrity_manifest(mod_dir)

    with TestClient(app) as client:
        registry.register(ModuleEntry(
            module_id=module_id, name=module_id, version="1.0.0",
            category="C", vendor="V", author="A", description="D",
            status=ModuleStatus.INSTALLED, install_date=datetime.now(),
            manifest_raw={"id": module_id, "checksum": "abc123sha256"}))

        try:
            resp = client.get(f"/api/v1/modules/{module_id}/sbom")
            body = resp.json()
        finally:
            registry.deregister(module_id)

    assert body["checksum"] == "abc123sha256"


def test_sbom_404_for_unknown_module():
    with TestClient(app) as client:
        resp = client.get("/api/v1/modules/ghost_module_9x/sbom")
        assert resp.status_code == 404
