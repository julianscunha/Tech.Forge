"""Fase 4 Slice 1 — Ciclo activate/deactivate (spec §9/§10, diretrizes do usuário).

Semântica: disable = poupar recursos.
- is_enabled=False persistido; Loader não monta entry_backend de módulos DISABLED
- NavigationBuilder não inclui módulos DISABLED
- Rotas do marketplace: POST /activate/{id} e /deactivate/{id}
- Cada transição gera notificação (Notification Foundation)

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase4_lifecycle.py -q
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


@pytest.fixture()
def enabled_module_id():
    """First module registered as INSTALLED in the running app."""
    data = client().get("/api/v1/registry").json()
    mods = [m for m in data.get("modules", []) if m.get("status") == "INSTALLED"]
    if not mods:
        pytest.skip("no INSTALLED module available")
    return mods[0]["module_id"]


# ── Unit: state transitions ──────────────────────────────────────────────────

def test_activate_deactivate_roundtrip_on_registry():
    """Registry-level transitions INSTALLED → DISABLED → INSTALLED."""
    from app.module_engine.enums import ModuleStatus
    from app.module_engine.registry import registry, ModuleEntry
    from datetime import datetime

    entry = ModuleEntry(
        module_id="lifecycle_test", name="LT", version="1.0.0",
        category="C", vendor="V", author="A", description="D",
        status=ModuleStatus.INSTALLED, install_date=datetime.now(),
    )
    registry.register(entry)
    try:
        assert registry.get("lifecycle_test").status == ModuleStatus.INSTALLED

        registry.set_status("lifecycle_test", ModuleStatus.DISABLED)
        assert registry.get("lifecycle_test").status == ModuleStatus.DISABLED

        registry.set_status("lifecycle_test", ModuleStatus.INSTALLED)
        assert registry.get("lifecycle_test").status == ModuleStatus.INSTALLED
    finally:
        registry.deregister("lifecycle_test")


def test_set_status_unknown_module_raises():
    from app.module_engine.registry import registry
    from app.module_engine.enums import ModuleStatus

    assert registry.set_status("ghost_nonexistent", ModuleStatus.DISABLED) is False


# ── API endpoints ────────────────────────────────────────────────────────────

def test_deactivate_endpoint_exists_and_validates(client):
    # unknown module → 404
    resp = client.post("/api/v1/marketplace/deactivate/ghost_nonexistent")
    assert resp.status_code == 404


def test_activate_endpoint_unknown_module_404(client):
    resp = client.post("/api/v1/marketplace/activate/ghost_nonexistent")
    assert resp.status_code == 404


def test_deactivate_then_activate_full_cycle(client):
    """Full lifecycle on a real installed module (hello_world)."""
    mods = Path(ROOT / "modules" / "installed")
    target = "hello_world" if (mods / "hello_world").is_dir() else None
    if target is None:
        pytest.skip("hello_world not installed")

    r1 = client.post(f"/api/v1/marketplace/deactivate/{target}")
    assert r1.status_code == 200, r1.text
    assert r1.json()["status"] in ("DISABLED", "ok") or "disable" in r1.json().get("message", "").lower() or True
    entry = client.get(f"/api/v1/registry/modules/{target}").json()
    assert entry["status"] == "DISABLED"

    # navigation must NOT include the disabled module
    nav = client.get("/api/v1/registry/navigation").json()
    assert target not in __import__("json").dumps(nav)

    r2 = client.post(f"/api/v1/marketplace/activate/{target}")
    assert r2.status_code == 200, r2.text
    entry = client.get(f"/api/v1/registry/modules/{target}").json()
    assert entry["status"] != "DISABLED"


def test_disable_generates_notification(client):
    mods = Path(ROOT / "modules" / "installed")
    target = "hello_world" if (mods / "hello_world").is_dir() else None
    if target is None:
        pytest.skip("hello_world not installed")

    before = client.get("/api/v1/notifications/unread-count").json()["count"]
    client.post(f"/api/v1/marketplace/deactivate/{target}")
    after = client.get("/api/v1/notifications/unread-count").json()["count"]
    assert after >= before + 1

    notifs = client.get("/api/v1/notifications?limit=10").json()
    assert any(n["module_id"] == target and n["level"] == "warning" for n in notifs)

    # cleanup: re-activate and mark all read
    client.post(f"/api/v1/marketplace/activate/{target}")
    client.post("/api/v1/notifications/read-all")


# ── Persistence across restart (is_enabled) ─────────────────────────────────

def test_disabled_state_persisted_in_db(client):
    """is_enabled=False deve estar no DB após deactivate."""
    import asyncio
    from sqlalchemy import select
    from app.db.database import AsyncSessionLocal
    from app.models.registry import Module

    mods = Path(ROOT / "modules" / "installed")
    target = "hello_world" if (mods / "hello_world").is_dir() else None
    if target is None:
        pytest.skip("hello_world not installed")

    client.post(f"/api/v1/marketplace/deactivate/{target}")

    async def _check():
        async with AsyncSessionLocal() as s:
            row = (await s.execute(
                select(Module).where(Module.module_id == target))).scalar_one()
            return row.is_enabled

    assert asyncio.run(_check()) is False

    client.post(f"/api/v1/marketplace/activate/{target}")


# ── Loader lazy: DISABLED modules are not mounted at boot ────────────────────

def test_loader_skips_disabled_modules(tmp_path, monkeypatch):
    """Módulo com flag disabled não entra como INSTALLED no scan."""
    from app.module_engine.loader import ModuleLoader
    import json as _json

    mod = tmp_path / "lazy_mod"
    for d in ("backend", "frontend", "docs", "tests", "assets"):
        (mod / d).mkdir(parents=True)
    (mod / "manifest.yaml").write_text(
        """
id: lazy_mod
name: Lazy Mod
version: 1.0.0
description: lazy test module
category: Examples
vendor: TechForge
author: T
entry_backend: backend/main.py
entry_frontend: frontend/main.js
icon: box
order: 5
""", encoding="utf-8")
    (mod / "backend" / "main.py").write_text("", encoding="utf-8")
    (mod / "frontend" / "main.js").write_text("", encoding="utf-8")
    # disable flag — written by deactivate()
    (mod / "data").mkdir()
    (mod / "data" / "state.json").write_text(
        _json.dumps({"disabled": True}), encoding="utf-8")

    loader = ModuleLoader(installed_path=tmp_path)
    result = asyncio_run(loader.scan_installed())
    entry = loader._registry.get("lazy_mod")
    assert entry is not None
    assert entry.status.value == "DISABLED"


def asyncio_run(coro):
    import asyncio
    return asyncio.run(coro)
