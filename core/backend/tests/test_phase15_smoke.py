"""Fase 15 Slice 13 — Smoke tests (spec §11).

Fluxo rápido pós-build: Start Platform → Health OK → Storage OK →
Discover Modules → Activate Test Module → Execute Basic Action. Usa
`hello_world` (módulo de referência, já instalado) em vez de instalar um
módulo novo — smoke test é sobre velocidade, o fluxo de instalação
completo já é coberto pelo E2E (test_phase15_e2e_module_lifecycle.py).

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase15_smoke.py -q
"""
from __future__ import annotations

from fastapi.testclient import TestClient

import pytest

from app.main import app

pytestmark = pytest.mark.smoke


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def test_smoke_start_health_storage_discover_activate_execute(client):
    # Start Platform — TestClient(app) já sobe via lifespan (fixture acima)

    # Health OK
    health = client.get("/api/v1/health")
    assert health.status_code == 200

    # Storage OK
    storage = client.get("/api/v1/system/storage/status")
    assert storage.status_code == 200
    assert storage.json()["database"] is True
    assert storage.json()["writable"] is True

    # Discover Modules
    registry_summary = client.get("/api/v1/registry/summary")
    assert registry_summary.status_code == 200
    assert registry_summary.json()["total"] >= 1

    # Activate Test Module — hello_world já é o módulo de referência ativo
    client.post("/api/v1/marketplace/activate/hello_world")

    # Execute Basic Action
    from app.service_registry.invoker import invoke

    result = invoke("hello_world", "ping")
    assert result["status"] == "ok"
