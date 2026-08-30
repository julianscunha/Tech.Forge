"""Fase 1 quality pass — R1: validação de entrada nos schemas.

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase1_validation.py -q
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


def test_register_module_rejects_empty_module_id(client):
    resp = client.post("/api/v1/modules", json={
        "module_id": "", "name": "X", "version": "1.0.0",
    })
    assert resp.status_code == 422


def test_register_module_rejects_empty_name(client):
    resp = client.post("/api/v1/modules", json={
        "module_id": "some_mod", "name": "", "version": "1.0.0",
    })
    assert resp.status_code == 422


def test_register_module_rejects_non_semver_version(client):
    resp = client.post("/api/v1/modules", json={
        "module_id": "some_mod", "name": "X", "version": "abc",
    })
    assert resp.status_code == 422


def test_register_module_rejects_bad_module_id_format(client):
    """module_id deve ser snake_case (mesma regra do ManifestParser)."""
    resp = client.post("/api/v1/modules", json={
        "module_id": "Bad Id!", "name": "X", "version": "1.0.0",
    })
    assert resp.status_code == 422


def test_register_module_accepts_valid_payload(client):
    import asyncio
    from sqlalchemy import delete
    from app.db.database import AsyncSessionLocal
    from app.models.registry import Module

    async def _clean():
        async with AsyncSessionLocal() as s:
            await s.execute(delete(Module).where(Module.module_id == "valid_mod"))
            await s.commit()
    asyncio.run(_clean())

    try:
        resp = client.post("/api/v1/modules", json={
            "module_id": "valid_mod", "name": "Valid", "version": "1.0.0",
            "category_id": None,
        })
        assert resp.status_code == 201, resp.text
    finally:
        asyncio.run(_clean())


def test_create_category_rejects_empty_slug(client):
    resp = client.post("/api/v1/categories", json={"slug": "", "name": "X"})
    assert resp.status_code == 422
