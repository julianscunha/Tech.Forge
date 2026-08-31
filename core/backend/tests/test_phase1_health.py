"""Health Check: GET /api/v1/platform/health.

Resposta deve identificar status, nome da plataforma e versão.

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase1_health.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))

from fastapi.testclient import TestClient

from app.main import app

pytestmark = pytest.mark.integration


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def test_platform_health_returns_status_platform_version(client):
    resp = client.get("/api/v1/platform/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["platform"] == "TechForge"
    assert data["version"]


def test_platform_health_reports_database_status(client):
    resp = client.get("/api/v1/platform/health")
    data = resp.json()
    assert data["database"] in {"connected", "error"}
