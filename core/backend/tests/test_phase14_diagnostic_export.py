"""
TechForge Fase 14 Slice 15 — Diagnostic snapshot + export
============================================================
"""
from __future__ import annotations

import json
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


class TestBuildSnapshot:

    @pytest.mark.asyncio
    async def test_snapshot_shape(self, client):
        from app.db.database import AsyncSessionLocal
        from app.services.diagnostic_export import DiagnosticExportService

        async with AsyncSessionLocal() as db:
            snapshot = await DiagnosticExportService.build_snapshot(db)

        assert set(snapshot.keys()) == {
            "generated_at", "platform_version", "system", "startup",
            "recent_errors", "recent_executions",
        }
        assert snapshot["platform_version"] == "1.0.0"
        assert isinstance(snapshot["recent_errors"], list)
        assert isinstance(snapshot["recent_executions"], list)


class TestJsonExport:

    def test_to_json_produces_valid_json(self):
        from app.services.diagnostic_export import DiagnosticExportService

        snapshot = {
            "generated_at": "2026-01-01T00:00:00Z", "platform_version": "1.0.0",
            "system": {"platform": {"database_status": "connected", "modules_installed": 1,
                                    "modules_enabled": 1}, "runtime": {"state": "ready"}},
            "startup": {"steps": {"a": 0.1}, "total_seconds": 0.1},
            "recent_errors": [], "recent_executions": [],
        }
        text = DiagnosticExportService.to_json(snapshot)
        parsed = json.loads(text)
        assert parsed["platform_version"] == "1.0.0"


class TestTxtExport:

    def test_to_txt_includes_key_sections(self):
        from app.services.diagnostic_export import DiagnosticExportService

        snapshot = {
            "generated_at": "2026-01-01T00:00:00Z", "platform_version": "1.0.0",
            "system": {"platform": {"database_status": "connected", "modules_installed": 2,
                                    "modules_enabled": 1}, "runtime": {"state": "ready"}},
            "startup": {"steps": {"database_init": 0.05}, "total_seconds": 0.05},
            "recent_errors": [{"code": "TF-EXECUTION-001", "source": "execution",
                               "message": "boom", "module_id": "hello_world"}],
            "recent_executions": [{"module_id": "hello_world", "status": "SUCCESS",
                                   "duration_seconds": 0.2}],
        }
        text = DiagnosticExportService.to_txt(snapshot)
        assert "TechForge Diagnostic Report" in text
        assert "Platform version: 1.0.0" in text
        assert "database_init: 0.05s" in text
        assert "TF-EXECUTION-001" in text
        assert "hello_world: SUCCESS" in text
