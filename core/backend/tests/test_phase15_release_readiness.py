"""Fase 15 Slice 9 — Release Readiness Report (spec §36/§37).

Tests/Build ficam de fora do agregador vivo (`compute_release_readiness`) —
rodar a suite inteira ou `npm run build` dentro do processo do próprio
servidor avaliado é pesado e circular. `techforge release-check` (CLI) roda
os dois via subprocess e combina com este relatório.

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase15_release_readiness.py -q
"""
from __future__ import annotations

from fastapi.testclient import TestClient

import pytest

from app.main import app

pytestmark = pytest.mark.integration


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def test_release_readiness_endpoint_returns_ready_report(client):
    response = client.get("/api/v1/release/readiness")
    assert response.status_code == 200
    body = response.json()
    assert body["version"]
    assert isinstance(body["ready"], bool)
    check_names = {c["name"] for c in body["checks"]}
    assert check_names == {"version_consistency", "changelog", "documentation", "migrations", "storage"}


def test_release_readiness_is_ready_on_clean_baseline(client):
    """Baseline atual (hello_world/veeam_m365, migrations em dia, CHANGELOG
    válido) deve reportar READY — regressão real se algum check quebrar."""
    response = client.get("/api/v1/release/readiness")
    body = response.json()
    failed = [c for c in body["checks"] if not c["passed"]]
    assert body["ready"] is True, f"checks falhando: {failed}"
