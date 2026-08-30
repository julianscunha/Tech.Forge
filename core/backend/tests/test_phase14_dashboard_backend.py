"""
TechForge Fase 14 Slice 18 (backend) — Resource usage + Heaviest modules
===========================================================================
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


class TestResourceUsageService:

    def test_snapshot_shape(self):
        from app.services.resource_usage import ResourceUsageService
        snap = ResourceUsageService.snapshot()
        assert set(snap.keys()) == {"cpu_percent", "memory_rss_bytes", "disk_used_bytes", "disk_total_bytes"}
        assert snap["memory_rss_bytes"] > 0
        assert snap["disk_total_bytes"] > 0


class TestHeaviestModulesService:

    @pytest.mark.asyncio
    async def test_snapshot_includes_disk_size_for_installed_module(self, client):
        from app.db.database import AsyncSessionLocal
        from app.services.execution_history import ExecutionHistoryService
        from app.services.heaviest_modules import HeaviestModulesService
        import uuid

        async with AsyncSessionLocal() as db:
            await ExecutionHistoryService.record(
                db, execution_id=str(uuid.uuid4()), module_id="hello_world",
                status="SUCCESS", duration_seconds=0.1,
            )
            results = await HeaviestModulesService.snapshot(db, limit=5)

        assert any(r["module_id"] == "hello_world" for r in results)
        entry = next(r for r in results if r["module_id"] == "hello_world")
        assert entry["disk_bytes"] > 0
        assert entry["execution_count"] >= 1

    @pytest.mark.asyncio
    async def test_snapshot_computes_failure_rate(self, client):
        from app.db.database import AsyncSessionLocal
        from app.services.execution_history import ExecutionHistoryService
        from app.services.heaviest_modules import HeaviestModulesService
        import uuid

        module_id = f"rate_test_{uuid.uuid4().hex[:8]}"
        async with AsyncSessionLocal() as db:
            await ExecutionHistoryService.record(db, execution_id=str(uuid.uuid4()), module_id=module_id,
                                                 status="SUCCESS", duration_seconds=0.1)
            await ExecutionHistoryService.record(db, execution_id=str(uuid.uuid4()), module_id=module_id,
                                                 status="FAILED", duration_seconds=0.1)
            results = await HeaviestModulesService.snapshot(db, limit=50)

        entry = next(r for r in results if r["module_id"] == module_id)
        assert entry["failure_rate"] == 0.5
        assert entry["disk_bytes"] == 0  # não instalado de verdade


class TestDiagnosticsResourcesEndpoint:

    def test_get_resources(self, client):
        resp = client.get("/api/v1/diagnostics/resources")
        assert resp.status_code == 200
        data = resp.json()
        assert "cpu_percent" in data
        assert "memory_rss_bytes" in data

    def test_get_heaviest_modules(self, client):
        resp = client.get("/api/v1/diagnostics/heaviest-modules")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
