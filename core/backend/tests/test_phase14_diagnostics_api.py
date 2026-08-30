"""
TechForge Fase 14 Slice 17 (parte 2) — API de diagnostics
============================================================
"""
from __future__ import annotations

import sys
import zipfile
from io import BytesIO
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))

from fastapi.testclient import TestClient

from app.main import app

pytestmark = pytest.mark.integration


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


class TestDiagnosticsEndpoints:

    def test_get_diagnostics(self, client):
        resp = client.get("/api/v1/diagnostics")
        assert resp.status_code == 200
        data = resp.json()
        assert set(data.keys()) == {"platform", "storage", "runtime", "modules"}

    def test_get_diagnostics_health(self, client):
        resp = client.get("/api/v1/diagnostics/health")
        assert resp.status_code == 200
        data = resp.json()
        assert set(data.keys()) == {"platform", "storage", "runtime"}

    def test_get_diagnostics_errors(self, client):
        resp = client.get("/api/v1/diagnostics/errors")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_diagnostics_errors_respects_limit(self, client):
        resp = client.get("/api/v1/diagnostics/errors?limit=1")
        assert resp.status_code == 200
        assert len(resp.json()) <= 1

    def test_get_diagnostics_executions(self, client):
        resp = client.get("/api/v1/diagnostics/executions")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_export_json(self, client):
        resp = client.post("/api/v1/diagnostics/export?format=json")
        assert resp.status_code == 200
        data = resp.json()
        assert "platform_version" in data

    def test_export_txt(self, client):
        resp = client.post("/api/v1/diagnostics/export?format=txt")
        assert resp.status_code == 200
        assert "TechForge Diagnostic Report" in resp.text

    def test_export_zip(self, client):
        resp = client.post("/api/v1/diagnostics/export?format=zip")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/zip"
        zf = zipfile.ZipFile(BytesIO(resp.content))
        assert "diagnostic_snapshot.json" in zf.namelist()

    def test_export_rejects_invalid_format(self, client):
        resp = client.post("/api/v1/diagnostics/export?format=xml")
        assert resp.status_code == 422


class TestModuleDiagnosticsEndpoints:

    def test_get_module_diagnostics(self, client):
        resp = client.get("/api/v1/modules/hello_world/diagnostics")
        assert resp.status_code == 200
        data = resp.json()
        assert data["module_id"] == "hello_world"
        assert "recent_errors" in data
        assert "recent_executions" in data

    def test_get_module_diagnostics_unknown_module_has_no_runtime(self, client):
        resp = client.get("/api/v1/modules/does_not_exist/diagnostics")
        assert resp.status_code == 200
        assert resp.json()["runtime"] is None

    def test_get_module_executions(self, client):
        resp = client.get("/api/v1/modules/hello_world/executions")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
