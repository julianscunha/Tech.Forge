"""Fase 17 Slice 5 — Audit events de segurança via EventBus (spec §36).

Cada evento tem um call-site real (não são disparados manualmente em
teste) — reusa o EventBus genérico da Fase 14, sem infraestrutura nova.
Nenhum valor sensível (assinatura crua, chave, conteúdo do manifest)
entra no payload — só module_id + status/motivo.

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase17_security_audit_events.py -q
"""
from __future__ import annotations

import asyncio
import base64
import zipfile
from datetime import datetime

import pytest
import yaml
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
from app.observability.events import event_bus
from app.schemas.publisher import PublisherCreate
from app.services.publisher import PublisherService
from tests.test_phase4 import MANIFEST_BASE, make_package_manager

pytestmark = pytest.mark.integration


class _Catcher:
    def __init__(self):
        self.events = []

    def __call__(self, event):
        self.events.append(event)


def _capture():
    catcher = _Catcher()
    event_bus.subscribe(catcher)
    return catcher


def test_package_verified_event_on_valid_integrity(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "MODULES_INSTALLED_PATH", tmp_path)
    module_id = "audit_package_verified_test"
    mod_dir = tmp_path / module_id
    (mod_dir / "backend").mkdir(parents=True)
    (mod_dir / "backend" / "main.py").write_text("x=1\n", encoding="utf-8")
    write_integrity_manifest(mod_dir)

    catcher = _capture()
    try:
        async def _run():
            async with AsyncSessionLocal() as db:
                from app.module_trust.verification import verify_module_integrity
                await verify_module_integrity(module_id, db)
        asyncio.run(_run())
    finally:
        event_bus.unsubscribe(catcher)

    verified = [e for e in catcher.events if e.type == "security.package_verified"]
    assert len(verified) == 1
    assert verified[0].payload == {"module_id": module_id}


def test_integrity_failure_event_on_modified_file(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "MODULES_INSTALLED_PATH", tmp_path)
    module_id = "audit_integrity_failure_test"
    mod_dir = tmp_path / module_id
    (mod_dir / "backend").mkdir(parents=True)
    (mod_dir / "backend" / "main.py").write_text("x=1\n", encoding="utf-8")
    write_integrity_manifest(mod_dir)
    (mod_dir / "backend" / "main.py").write_text("x=2\n", encoding="utf-8")  # tamper

    catcher = _capture()
    try:
        async def _run():
            async with AsyncSessionLocal() as db:
                from app.module_trust.verification import verify_module_integrity
                await verify_module_integrity(module_id, db)
        asyncio.run(_run())
    finally:
        event_bus.unsubscribe(catcher)

    failures = [e for e in catcher.events if e.type == "security.integrity_failure"]
    assert len(failures) == 1
    assert failures[0].payload["module_id"] == module_id
    assert failures[0].payload["status"] == "MODIFIED"


def test_signature_valid_and_invalid_events(tmp_path, monkeypatch):
    module_id = "audit_signature_test"
    publisher_id = "audit_signature_publisher"
    private_pem, public_pem = generate_ed25519_keypair()

    with TestClient(app) as client:
        monkeypatch.setattr(settings, "MODULES_INSTALLED_PATH", tmp_path)
        mod_dir = tmp_path / module_id
        (mod_dir / "backend").mkdir(parents=True)
        (mod_dir / "backend" / "main.py").write_text("x=1\n", encoding="utf-8")
        write_integrity_manifest(mod_dir)

        signed_raw = {"id": module_id, "publisher": {"id": publisher_id}}
        signature = Ed25519SignatureProvider().sign(canonical_manifest_bytes(signed_raw), private_pem)
        valid_raw = {**signed_raw, "signature": base64.b64encode(signature).decode()}

        registry.register(ModuleEntry(
            module_id=module_id, name=module_id, version="1.0.0",
            category="C", vendor="V", author="A", description="D",
            status=ModuleStatus.INSTALLED, install_date=datetime.now(),
            manifest_raw=valid_raw))

        async def _setup_publisher():
            async with AsyncSessionLocal() as db:
                await db.execute(delete(Publisher).where(Publisher.id == publisher_id))
                await db.commit()
                await PublisherService.register(db, PublisherCreate(
                    id=publisher_id, name="Audit Test Publisher", type="THIRD_PARTY",
                    public_key=public_pem.decode(), trust_status="TRUSTED"))
        asyncio.run(_setup_publisher())

        catcher = _capture()
        try:
            resp = client.get(f"/api/v1/modules/{module_id}/trust")
            assert resp.status_code == 200
            assert resp.json()["signature_status"] == "VALID"

            # Adultera o manifesto em memória (registry) — assinatura nao bate mais
            registry.register(ModuleEntry(
                module_id=module_id, name=module_id, version="1.0.0",
                category="C", vendor="V", author="A", description="D",
                status=ModuleStatus.INSTALLED, install_date=datetime.now(),
                manifest_raw={**valid_raw, "description": "tampered"}))
            resp2 = client.get(f"/api/v1/modules/{module_id}/trust")
            assert resp2.json()["signature_status"] == "INVALID"
        finally:
            registry.deregister(module_id)
            event_bus.unsubscribe(catcher)
            async def _cleanup():
                async with AsyncSessionLocal() as db:
                    await db.execute(delete(Publisher).where(Publisher.id == publisher_id))
                    await db.commit()
            asyncio.run(_cleanup())

    valid_events = [e for e in catcher.events if e.type == "security.signature_valid"]
    invalid_events = [e for e in catcher.events if e.type == "security.signature_invalid"]
    assert len(valid_events) == 1
    assert valid_events[0].payload == {"module_id": module_id}
    assert len(invalid_events) == 1
    assert invalid_events[0].payload == {"module_id": module_id}

    # Nenhum payload carrega a assinatura crua, chave publica ou conteudo do manifest.
    for e in valid_events + invalid_events:
        assert set(e.payload.keys()) == {"module_id"}


def test_module_trust_changed_event_on_transition(tmp_path, monkeypatch):
    module_id = "audit_trust_changed_test"

    with TestClient(app) as client:
        monkeypatch.setattr(settings, "MODULES_INSTALLED_PATH", tmp_path)
        mod_dir = tmp_path / module_id
        (mod_dir / "backend").mkdir(parents=True)
        (mod_dir / "backend" / "main.py").write_text("x=1\n", encoding="utf-8")
        write_integrity_manifest(mod_dir)

        registry.register(ModuleEntry(
            module_id=module_id, name=module_id, version="1.0.0",
            category="C", vendor="V", author="A", description="D",
            status=ModuleStatus.INSTALLED, install_date=datetime.now(),
            manifest_raw={"id": module_id}))

        catcher = _capture()
        try:
            first = client.get(f"/api/v1/modules/{module_id}/trust").json()
            assert first["trust_level"] == "UNVERIFIED"

            # Tampera o arquivo em disco -> integridade MODIFIED -> trust_level muda
            (mod_dir / "backend" / "main.py").write_text("x=2\n", encoding="utf-8")
            second = client.get(f"/api/v1/modules/{module_id}/trust").json()
            assert second["trust_level"] == "MODIFIED"
        finally:
            registry.deregister(module_id)
            event_bus.unsubscribe(catcher)

    changed = [e for e in catcher.events if e.type == "security.module_trust_changed"]
    assert len(changed) == 1
    assert changed[0].payload == {
        "module_id": module_id, "from": "UNVERIFIED", "to": "MODIFIED"}


def test_module_blocked_event_on_oversized_package(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "MAX_PACKAGE_UNCOMPRESSED_SIZE", 1_000)

    pm = make_package_manager(tmp_path)
    module_id = "audit_blocked_test"
    manifest = {**MANIFEST_BASE, "id": module_id}
    mod_path = tmp_path / f"{module_id}-1.0.0.mod"
    with zipfile.ZipFile(mod_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.yaml", yaml.dump(manifest))
        zf.writestr("backend/bomb.bin", b"0" * 50_000)

    catcher = _capture()
    try:
        asyncio.run(pm.install(mod_path))
    finally:
        event_bus.unsubscribe(catcher)

    blocked = [e for e in catcher.events if e.type == "security.module_blocked"]
    assert len(blocked) == 1
    assert blocked[0].payload["module_id"] == module_id
    assert "reason" in blocked[0].payload
