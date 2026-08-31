"""Fase 17 Slice 4 — GET /api/v1/security/status e /security/publishers.

Agrega dados já existentes (Trust Level por módulo via list_modules_trust,
Publisher Registry) — nenhuma lógica de trust duplicada aqui, só
contagem/reexposição sob o prefixo pedido pelo spec (§44/§45).

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase17_security_status.py -q
"""
from __future__ import annotations

import asyncio
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.db.database import AsyncSessionLocal
from app.main import app
from app.models.publisher import Publisher
from app.module_engine.enums import ModuleStatus
from app.module_engine.registry import ModuleEntry, registry
from app.schemas.publisher import PublisherCreate
from app.services.publisher import PublisherService

pytestmark = pytest.mark.integration


def _register_publisher(publisher_id: str, trust_status: str) -> None:
    async def _run():
        async with AsyncSessionLocal() as db:
            await db.execute(delete(Publisher).where(Publisher.id == publisher_id))
            await db.commit()
            await PublisherService.register(db, PublisherCreate(
                id=publisher_id, name="Security Status Test Publisher",
                type="THIRD_PARTY", trust_status=trust_status))
    asyncio.run(_run())


def _cleanup_publisher(publisher_id: str) -> None:
    async def _run():
        async with AsyncSessionLocal() as db:
            await db.execute(delete(Publisher).where(Publisher.id == publisher_id))
            await db.commit()
    asyncio.run(_run())


def test_security_status_counts_by_trust_level(tmp_path, monkeypatch):
    from app.core.settings import settings

    module_id = "security_status_test_mod"

    with TestClient(app) as client:
        monkeypatch.setattr(settings, "MODULES_INSTALLED_PATH", tmp_path)
        mod_dir = tmp_path / module_id
        (mod_dir / "backend").mkdir(parents=True)
        (mod_dir / "backend" / "main.py").write_text("x=1\n", encoding="utf-8")
        from app.module_trust.integrity import write_integrity_manifest
        write_integrity_manifest(mod_dir)

        entry = ModuleEntry(
            module_id=module_id, name=module_id, version="1.0.0",
            category="C", vendor="V", author="A", description="D",
            status=ModuleStatus.INSTALLED, install_date=datetime.now(),
            manifest_raw={"id": module_id})
        registry.register(entry)

        try:
            resp = client.get("/api/v1/security/status")
            assert resp.status_code == 200
            body = resp.json()
            assert "by_trust_level" in body
            assert body["by_trust_level"]["UNVERIFIED"] >= 1
            assert body["total_modules"] >= 1
            assert "unsigned_count" in body
            assert body["unsigned_count"] >= 1
            assert "revoked_publishers" in body
        finally:
            registry.deregister(module_id)


def test_security_status_counts_revoked_publishers():
    publisher_id = "security_status_revoked_publisher"
    _register_publisher(publisher_id, "REVOKED")

    try:
        with TestClient(app) as client:
            resp = client.get("/api/v1/security/status")
            assert resp.status_code == 200
            assert resp.json()["revoked_publishers"] >= 1
    finally:
        _cleanup_publisher(publisher_id)


def test_security_publishers_matches_publishers_endpoint():
    publisher_id = "security_publishers_alias_test"
    _register_publisher(publisher_id, "TRUSTED")

    try:
        with TestClient(app) as client:
            direct = client.get("/api/v1/publishers").json()
            via_security = client.get("/api/v1/security/publishers").json()
            assert direct == via_security
            assert any(p["id"] == publisher_id for p in via_security)
    finally:
        _cleanup_publisher(publisher_id)
