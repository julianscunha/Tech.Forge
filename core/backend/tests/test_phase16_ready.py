"""Fase 16 Slice 2 — GET /ready distinto de /health (spec §15/§35/§42).

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase16_ready.py -q
"""
from __future__ import annotations

from fastapi.testclient import TestClient

import pytest

from app.main import app
from app.runtime import RuntimeState, runtime

pytestmark = pytest.mark.integration


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def test_ready_returns_200_when_runtime_is_ready(client, monkeypatch):
    # runtime é um singleton global compartilhado entre testes — outros
    # testes que já saíram do `with TestClient(app)` deixam o estado em
    # STOPPED (fire_shutdown), então fixamos READY explicitamente em vez
    # de assumir a ordem de execução da suíte.
    monkeypatch.setattr(runtime, "state", RuntimeState.READY)
    response = client.get("/api/v1/platform/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["ready"] is True
    assert body["state"] == "ready"


def test_ready_returns_503_when_runtime_not_ready(client, monkeypatch):
    monkeypatch.setattr(runtime, "state", RuntimeState.BOOTSTRAPPING)
    response = client.get("/api/v1/platform/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["ready"] is False
    assert body["state"] == "bootstrapping"
