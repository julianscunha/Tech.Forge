"""Fase 12 Slice 10 — Data portability: export de configuração (spec §16/§29).

`GET /api/v1/config` — configuração de plataforma efetiva (lacuna do §29
nunca fechada em slice anterior). Como plataforma não guarda segredos em
`settings.py` (spec §9 exige isso), o mesmo payload já serve de "export"
(§16) — não precisa de endpoint /export separado.

Export de módulo já é coberto por `GET /modules/{id}/config` (Slice 4) —
este arquivo só formaliza esse contrato com um teste nomeado como "export".

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase12_platform_config.py -q
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


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def test_get_platform_config_returns_effective_settings(client):
    resp = client.get("/api/v1/config")
    assert resp.status_code == 200
    data = resp.json()
    assert data["PLATFORM_NAME"] == "TechForge"
    assert data["HOST"]
    assert isinstance(data["PORT"], int)


def test_get_platform_config_paths_are_json_strings_not_objects(client):
    resp = client.get("/api/v1/config")
    data = resp.json()
    assert isinstance(data["MODULES_INSTALLED_PATH"], str)
    assert isinstance(data["LOGS_PATH"], str)


MODULE_ID = "export_test_module"
MANIFEST_RAW = {
    "configuration": {"fields": [{"id": "retention_days", "type": "integer", "default": 30}]},
}


@pytest.fixture()
def registered_module():
    async def _delete():
        from app.db.database import AsyncSessionLocal
        from app.models.module_configuration import ModuleConfiguration
        async with AsyncSessionLocal() as db:
            row = await db.get(ModuleConfiguration, MODULE_ID)
            if row is not None:
                await db.delete(row)
                await db.commit()

    import asyncio
    asyncio.run(_delete())
    entry = ModuleEntry(
        module_id=MODULE_ID, name="Export Test", version="1.0.0",
        category="C", vendor="V", author="A", description="D",
        status=ModuleStatus.INSTALLED, install_date=datetime.now(),
        manifest_raw=MANIFEST_RAW,
    )
    registry.register(entry)
    yield entry
    registry.deregister(MODULE_ID)
    asyncio.run(_delete())


def test_module_config_export_reproduces_saved_values_exactly(client, registered_module):
    """Spec §16 aceite: export de um módulo com config salva reproduz os
    valores exatos via JSON. `GET /modules/{id}/config` já é esse contrato
    (Slice 4) — não precisa de endpoint /export duplicado."""
    client.put(f"/api/v1/modules/{MODULE_ID}/config", json={"values": {"retention_days": 45}})

    resp = client.get(f"/api/v1/modules/{MODULE_ID}/config")
    assert resp.status_code == 200
    exported = resp.json()
    assert exported["module_id"] == MODULE_ID
    assert exported["values"] == {"retention_days": 45}
