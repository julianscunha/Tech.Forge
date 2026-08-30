"""Fase 12 Slice 1 — Storage abstraction + health.

Spec docs/phases/12 §3 (Storage Provider) e §24 (Persistence health):
GET /api/v1/system/storage/status deve reportar se o banco está disponível
e se é gravável.

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase12_storage.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))

from fastapi.testclient import TestClient

from app.main import app
from app.db.database import AsyncSessionLocal
from app.db.storage import StorageProvider

pytestmark = pytest.mark.integration


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def test_storage_status_endpoint_reports_database_and_writable(client):
    resp = client.get("/api/v1/system/storage/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["database"] is True
    assert data["writable"] is True


@pytest.mark.asyncio
async def test_storage_provider_health_check_reports_writable_true_on_healthy_db():
    provider = StorageProvider()
    async with AsyncSessionLocal() as session:
        health = await provider.health_check(session)
    assert health.database is True
    assert health.writable is True
