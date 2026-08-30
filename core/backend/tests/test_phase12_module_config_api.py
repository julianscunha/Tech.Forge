"""Fase 12 Slice 4 — Module configuration API (spec §29).

GET/PUT /api/v1/modules/{id}/config, POST /api/v1/modules/{id}/config/validate.
Fonte dos campos é o registry in-memory (manifest_raw) — mesma fonte única
de verdade das demais APIs de módulo.

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase12_module_config_api.py -q
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))

from fastapi.testclient import TestClient

from app.main import app
from app.module_engine.enums import ModuleStatus
from app.module_engine.registry import ModuleEntry, registry

pytestmark = pytest.mark.integration

MODULE_ID = "cfg_api_test"

MANIFEST_RAW = {
    "configuration": {"fields": [
        {"id": "retention_days", "type": "integer", "default": 30},
    ]},
}


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


async def _delete_config_row():
    from app.db.database import AsyncSessionLocal
    from app.models.module_configuration import ModuleConfiguration

    async with AsyncSessionLocal() as db:
        row = await db.get(ModuleConfiguration, MODULE_ID)
        if row is not None:
            await db.delete(row)
            await db.commit()


@pytest.fixture()
def registered_module():
    import asyncio

    asyncio.run(_delete_config_row())  # testes rodam contra o banco real de dev
    entry = ModuleEntry(
        module_id=MODULE_ID, name="Cfg Api Test", version="1.0.0",
        category="C", vendor="V", author="A", description="D",
        status=ModuleStatus.INSTALLED, install_date=datetime.now(),
        manifest_raw=MANIFEST_RAW,
    )
    registry.register(entry)
    yield entry
    registry.deregister(MODULE_ID)
    asyncio.run(_delete_config_row())


def test_get_config_returns_defaults_when_never_saved(client, registered_module):
    resp = client.get(f"/api/v1/modules/{MODULE_ID}/config")
    assert resp.status_code == 200
    assert resp.json()["values"] == {"retention_days": 30}


def test_put_config_persists_valid_values(client, registered_module):
    resp = client.put(f"/api/v1/modules/{MODULE_ID}/config", json={"values": {"retention_days": 7}})
    assert resp.status_code == 200
    assert resp.json()["values"] == {"retention_days": 7}

    resp2 = client.get(f"/api/v1/modules/{MODULE_ID}/config")
    assert resp2.json()["values"] == {"retention_days": 7}


def test_put_config_rejects_invalid_value(client, registered_module):
    resp = client.put(f"/api/v1/modules/{MODULE_ID}/config", json={"values": {"retention_days": "bad"}})
    assert resp.status_code == 422


def test_validate_config_does_not_persist(client, registered_module):
    resp = client.post(f"/api/v1/modules/{MODULE_ID}/config/validate", json={"values": {"retention_days": 99}})
    assert resp.status_code == 200
    assert resp.json()["valid"] is True

    resp2 = client.get(f"/api/v1/modules/{MODULE_ID}/config")
    assert resp2.json()["values"] == {"retention_days": 30}  # ainda no default


def test_config_endpoints_404_for_unknown_module(client):
    resp = client.get("/api/v1/modules/does_not_exist/config")
    assert resp.status_code == 404
