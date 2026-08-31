"""Fase 17 Slice 2 — assinatura Ed25519 real integrada em GET /modules/{id}/trust.

Prova que a assinatura Ed25519 é verificada de ponta a ponta pela rota
real (não só a função isolada `Ed25519SignatureProvider`): assinatura
válida contra a `public_key` do publisher -> VALID (e TRUSTED quando o
publisher também é TRUSTED); pacote adulterado depois de assinado ->
INVALID.

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase17_signature_integration.py -q
"""
from __future__ import annotations

import asyncio
import base64
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.core.settings import settings
from app.db.database import AsyncSessionLocal
from app.main import app
from app.models.publisher import Publisher
from app.module_engine.enums import ModuleStatus
from app.module_engine.registry import ModuleEntry, registry
from app.module_trust.integrity import write_integrity_manifest
from app.module_trust.signature import (
    Ed25519SignatureProvider,
    canonical_manifest_bytes,
    generate_ed25519_keypair,
)
from app.schemas.publisher import PublisherCreate
from app.services.publisher import PublisherService

pytestmark = pytest.mark.integration


def _register_publisher(publisher_id: str, public_key_pem: bytes, trust_status: str) -> None:
    async def _run():
        async with AsyncSessionLocal() as db:
            await db.execute(delete(Publisher).where(Publisher.id == publisher_id))
            await db.commit()
            await PublisherService.register(db, PublisherCreate(
                id=publisher_id, name="Ed25519 Test Publisher", type="THIRD_PARTY",
                public_key=public_key_pem.decode(), trust_status=trust_status))
    asyncio.run(_run())


def _cleanup_publisher(publisher_id: str) -> None:
    async def _run():
        async with AsyncSessionLocal() as db:
            await db.execute(delete(Publisher).where(Publisher.id == publisher_id))
            await db.commit()
    asyncio.run(_run())


def test_valid_ed25519_signature_reaches_trusted(tmp_path, monkeypatch):
    module_id = "ed25519_trust_test"
    publisher_id = "ed25519_trusted_publisher"
    private_pem, public_pem = generate_ed25519_keypair()

    with TestClient(app) as client:
        monkeypatch.setattr(settings, "MODULES_INSTALLED_PATH", tmp_path)
        mod_dir = tmp_path / module_id
        (mod_dir / "backend").mkdir(parents=True)
        (mod_dir / "backend" / "main.py").write_text("x=1\n", encoding="utf-8")
        write_integrity_manifest(mod_dir)

        manifest_raw = {"id": module_id, "publisher": {"id": publisher_id}}
        signature = Ed25519SignatureProvider().sign(canonical_manifest_bytes(manifest_raw), private_pem)
        manifest_raw["signature"] = base64.b64encode(signature).decode()

        entry = ModuleEntry(
            module_id=module_id, name=module_id, version="1.0.0",
            category="C", vendor="V", author="A", description="D",
            status=ModuleStatus.INSTALLED, install_date=datetime.now(),
            manifest_raw=manifest_raw)
        registry.register(entry)
        _register_publisher(publisher_id, public_pem, "TRUSTED")

        try:
            resp = client.get(f"/api/v1/modules/{module_id}/trust")
            assert resp.status_code == 200
            body = resp.json()
            assert body["signature_status"] == "VALID"
            assert body["trust_level"] == "TRUSTED"
        finally:
            registry.deregister(module_id)
            _cleanup_publisher(publisher_id)


def test_tampered_manifest_invalidates_signature(tmp_path, monkeypatch):
    module_id = "ed25519_tampered_test"
    publisher_id = "ed25519_tampered_publisher"
    private_pem, public_pem = generate_ed25519_keypair()

    with TestClient(app) as client:
        monkeypatch.setattr(settings, "MODULES_INSTALLED_PATH", tmp_path)
        mod_dir = tmp_path / module_id
        (mod_dir / "backend").mkdir(parents=True)
        (mod_dir / "backend" / "main.py").write_text("x=1\n", encoding="utf-8")
        write_integrity_manifest(mod_dir)

        signed_raw = {"id": module_id, "publisher": {"id": publisher_id}}
        signature = Ed25519SignatureProvider().sign(canonical_manifest_bytes(signed_raw), private_pem)

        # Manifest registrado no runtime foi adulterado depois de assinado
        # (ex.: campo alterado) — a assinatura não cobre mais este conteúdo.
        tampered_raw = {
            "id": module_id, "publisher": {"id": publisher_id},
            "description": "injected after signing",
            "signature": base64.b64encode(signature).decode(),
        }

        entry = ModuleEntry(
            module_id=module_id, name=module_id, version="1.0.0",
            category="C", vendor="V", author="A", description="D",
            status=ModuleStatus.INSTALLED, install_date=datetime.now(),
            manifest_raw=tampered_raw)
        registry.register(entry)
        _register_publisher(publisher_id, public_pem, "TRUSTED")

        try:
            resp = client.get(f"/api/v1/modules/{module_id}/trust")
            assert resp.status_code == 200
            body = resp.json()
            assert body["signature_status"] == "INVALID"
            assert body["trust_level"] == "VERIFIED"  # nao TRUSTED, mas integridade dos arquivos continua ok
        finally:
            registry.deregister(module_id)
            _cleanup_publisher(publisher_id)
