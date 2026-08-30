"""
TechForge Fase 14 Slice 12 — SystemDiagnosticService
=======================================================
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))

from fastapi.testclient import TestClient

from app.main import app

pytestmark = pytest.mark.integration


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


class TestSystemDiagnosticServiceSnapshot:

    @pytest.mark.asyncio
    async def test_snapshot_shape(self, client):
        from app.db.database import AsyncSessionLocal
        from app.services.system_diagnostics import SystemDiagnosticService

        async with AsyncSessionLocal() as db:
            snapshot = await SystemDiagnosticService.snapshot(db)

        assert set(snapshot.keys()) == {"platform", "storage", "runtime", "modules"}

        assert snapshot["platform"]["name"] == "TechForge"
        assert snapshot["platform"]["database_status"] == "connected"
        assert isinstance(snapshot["platform"]["modules_installed"], int)

        assert snapshot["storage"]["database"] is True
        assert snapshot["storage"]["writable"] is True

        assert "state" in snapshot["runtime"]
        assert "events" in snapshot["runtime"]

        assert isinstance(snapshot["modules"], list)

    @pytest.mark.asyncio
    async def test_snapshot_includes_module_runtime_entries(self, client):
        from app.db.database import AsyncSessionLocal
        from app.module_runtime.state import RuntimeState, module_runtime_registry
        from app.services.system_diagnostics import SystemDiagnosticService

        module_runtime_registry.set_state("hello_world", RuntimeState.READY)
        try:
            async with AsyncSessionLocal() as db:
                snapshot = await SystemDiagnosticService.snapshot(db)
            module_ids = [m["module_id"] for m in snapshot["modules"]]
            assert "hello_world" in module_ids
            entry = next(m for m in snapshot["modules"] if m["module_id"] == "hello_world")
            assert entry["state"] == "READY"
        finally:
            module_runtime_registry.clear_transient_state()
