"""
TechForge Fase 14 Slice 13 — Failure correlation
===================================================
"""
from __future__ import annotations

import sys
import uuid
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


class TestFailureCorrelation:

    @pytest.mark.asyncio
    async def test_returns_none_for_unknown_error_id(self, client):
        from app.db.database import AsyncSessionLocal
        from app.services.failure_correlation import FailureCorrelationService

        async with AsyncSessionLocal() as db:
            result = await FailureCorrelationService.correlate(db, 999_999)
        assert result is None

    @pytest.mark.asyncio
    async def test_correlates_error_with_execution_and_module_state(self, client):
        from app.db.database import AsyncSessionLocal
        from app.module_runtime.state import RuntimeState, module_runtime_registry
        from app.services.error_registry import ErrorRegistryService
        from app.services.execution_history import ExecutionHistoryService
        from app.services.failure_correlation import FailureCorrelationService

        execution_id = str(uuid.uuid4())  # roda contra o DB real da app; precisa ser único por run
        module_runtime_registry.set_state("hello_world", RuntimeState.DEGRADED, last_error="boom")
        try:
            async with AsyncSessionLocal() as db:
                await ExecutionHistoryService.record(
                    db, execution_id=execution_id, module_id="hello_world",
                    status="FAILED", duration_seconds=0.5,
                )
                error = await ErrorRegistryService.record(
                    db, source="execution", message="boom",
                    module_id="hello_world", execution_id=execution_id,
                )

            async with AsyncSessionLocal() as db:
                result = await FailureCorrelationService.correlate(db, error.id)

            assert result["error"]["message"] == "boom"
            assert result["error"]["code"] == "TF-EXECUTION-001"
            assert result["execution"]["execution_id"] == execution_id
            assert result["execution"]["status"] == "FAILED"
            assert result["module_runtime"]["state"] == "DEGRADED"
            assert result["module_runtime"]["last_error"] == "boom"
            assert isinstance(result["dependents"], list)
            assert isinstance(result["recent_operations"], list)
            assert isinstance(result["recent_runtime_events"], list)
        finally:
            module_runtime_registry.clear_transient_state()

    @pytest.mark.asyncio
    async def test_handles_error_without_module_or_execution(self, client):
        from app.db.database import AsyncSessionLocal
        from app.services.error_registry import ErrorRegistryService
        from app.services.failure_correlation import FailureCorrelationService

        async with AsyncSessionLocal() as db:
            error = await ErrorRegistryService.record(db, source="runtime", message="component died")

        async with AsyncSessionLocal() as db:
            result = await FailureCorrelationService.correlate(db, error.id)

        assert result["execution"] is None
        assert result["module_runtime"] is None
        assert result["dependents"] == []
        assert result["recent_operations"] == []
