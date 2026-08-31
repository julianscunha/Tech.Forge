"""Fase 16 Slice 6 — Developer Mode real: paths reais + rescan (spec §38).

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase16_developer_mode.py -q
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


def test_diagnostics_snapshot_includes_install_and_user_data_paths(client):
    response = client.get("/api/v1/diagnostics")
    assert response.status_code == 200
    paths = response.json()["platform"]["paths"]
    assert "install_dir" in paths
    assert "user_data_dir" in paths


def test_rescan_endpoint_reloads_registry(client):
    response = client.post("/api/v1/registry/rescan")
    assert response.status_code == 200
    body = response.json()
    assert "installed" in body
