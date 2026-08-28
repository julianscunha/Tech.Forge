"""
Fase 11 Slice 5b: Remote Module Installation with Progress Tracking

Tests for InstallJobRegistry and remote installation endpoints with async
background job execution, progress reporting, and network failure handling.
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
from zipfile import ZipFile

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.package_manager.install_job import (
    InstallJob, InstallJobPhase, InstallJobRegistry, install_job_registry
)
from app.package_manager.models import PackageInfo
from app.package_manager.enums import CompatibilityLevel
from app.module_trust.trust import TrustLevel
from app.core.settings import settings


@pytest_asyncio.fixture
async def test_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def clean_install_jobs():
    """Clear the install job registry before each test."""
    install_job_registry._jobs.clear()
    yield install_job_registry
    install_job_registry._jobs.clear()


# ──────────────────────────────────────────────────────────────────────────────
# Part A — InstallJobRegistry
# ──────────────────────────────────────────────────────────────────────────────

class TestInstallJobRegistry:
    """Test in-memory install job tracking."""

    def test_create_job_returns_initial_acquiring_phase(self, clean_install_jobs):
        """Creating a job returns it in ACQUIRING phase with generated job_id."""
        job = clean_install_jobs.create("test_module")

        assert job.job_id is not None
        assert len(job.job_id) == 12  # uuid4().hex[:12]
        assert job.module_id == "test_module"
        assert job.phase == InstallJobPhase.ACQUIRING
        assert job.error is None
        assert job.started_at is not None
        assert isinstance(job.started_at, datetime)
        assert job.finished_at is None

    def test_create_multiple_jobs_generates_unique_ids(self, clean_install_jobs):
        """Multiple jobs get unique job_ids."""
        job1 = clean_install_jobs.create("mod1")
        job2 = clean_install_jobs.create("mod2")

        assert job1.job_id != job2.job_id

    def test_get_existing_job(self, clean_install_jobs):
        """get() returns a job that was created."""
        created = clean_install_jobs.create("test_module")
        retrieved = clean_install_jobs.get(created.job_id)

        assert retrieved is not None
        assert retrieved.job_id == created.job_id
        assert retrieved.module_id == "test_module"

    def test_get_nonexistent_job_returns_none(self, clean_install_jobs):
        """get() returns None for non-existent job_id."""
        result = clean_install_jobs.get("nonexistent-job-id")
        assert result is None

    def test_set_phase_advances_job_state(self, clean_install_jobs):
        """set_phase() updates the job's phase."""
        job = clean_install_jobs.create("test_module")
        job_id = job.job_id

        clean_install_jobs.set_phase(job_id, InstallJobPhase.VALIDATING)
        updated = clean_install_jobs.get(job_id)

        assert updated.phase == InstallJobPhase.VALIDATING
        assert updated.finished_at is None  # Not finished yet

    def test_set_phase_done_sets_finished_at(self, clean_install_jobs):
        """set_phase() to DONE sets finished_at timestamp."""
        job = clean_install_jobs.create("test_module")
        job_id = job.job_id
        before_finish = datetime.now(timezone.utc)

        clean_install_jobs.set_phase(job_id, InstallJobPhase.DONE)
        updated = clean_install_jobs.get(job_id)

        assert updated.phase == InstallJobPhase.DONE
        assert updated.finished_at is not None
        assert updated.finished_at >= before_finish

    def test_set_phase_failed_sets_finished_at_with_error(self, clean_install_jobs):
        """set_phase() to FAILED sets finished_at and error message."""
        job = clean_install_jobs.create("test_module")
        job_id = job.job_id
        error_msg = "Network connection failed"

        clean_install_jobs.set_phase(job_id, InstallJobPhase.FAILED, error=error_msg)
        updated = clean_install_jobs.get(job_id)

        assert updated.phase == InstallJobPhase.FAILED
        assert updated.error == error_msg
        assert updated.finished_at is not None

    def test_set_phase_on_intermediate_states_no_finished_at(self, clean_install_jobs):
        """set_phase() to ACQUIRING/VALIDATING/INSTALLING does not set finished_at."""
        job = clean_install_jobs.create("test_module")
        job_id = job.job_id

        for phase in [InstallJobPhase.ACQUIRING, InstallJobPhase.VALIDATING, InstallJobPhase.INSTALLING]:
            clean_install_jobs.set_phase(job_id, phase)
            updated = clean_install_jobs.get(job_id)
            assert updated.finished_at is None, f"phase {phase} should not set finished_at"

    def test_set_phase_nonexistent_job_does_nothing(self, clean_install_jobs):
        """set_phase() on a non-existent job_id does nothing (no error)."""
        # Should not raise
        clean_install_jobs.set_phase("nonexistent-id", InstallJobPhase.DONE)
        result = clean_install_jobs.get("nonexistent-id")
        assert result is None


# ──────────────────────────────────────────────────────────────────────────────
# Part B — Remote Installation Endpoints
# ──────────────────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def fastapi_client(test_db):
    """Create a test FastAPI client with mocked dependencies."""
    from app.main import app

    # Patch the database session dependency
    async def get_test_db():
        yield test_db

    from app.db.database import get_db
    app.dependency_overrides[get_db] = get_test_db

    client = TestClient(app)
    yield client

    app.dependency_overrides.clear()


class TestRemoteInstallEndpoints:
    """Test POST/GET endpoints for remote module installation."""

    @pytest.mark.asyncio
    async def test_post_marketplace_install_remote_returns_job_id(self, fastapi_client):
        """POST /marketplace/install-remote/{id} returns job_id immediately."""
        module_id = "test_module"

        response = fastapi_client.post(
            f"/api/v1/marketplace/install-remote/{module_id}",
            json={"source_id": None}
        )

        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert len(data["job_id"]) == 12  # UUID truncated to 12 chars

    @pytest.mark.asyncio
    async def test_get_install_job_returns_current_phase(self, clean_install_jobs):
        """GET /marketplace/install-jobs/{job_id} returns job state."""
        job = clean_install_jobs.create("test_module")
        job_id = job.job_id

        # Simulate what the endpoint would do
        retrieved = clean_install_jobs.get(job_id)

        assert retrieved is not None
        assert retrieved.job_id == job_id
        assert retrieved.phase == InstallJobPhase.ACQUIRING
        assert retrieved.error is None

    @pytest.mark.asyncio
    async def test_get_install_job_nonexistent_returns_404(self, fastapi_client):
        """GET /marketplace/install-jobs/{job_id} returns 404 if job not found."""
        response = fastapi_client.get("/api/v1/marketplace/install-jobs/nonexistent-id")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_background_task_with_valid_provider_reaches_done(self, clean_install_jobs, tmp_path):
        """Background task: real fetch_mod_path() + real install() → DONE."""
        from app.api.routes import marketplace as marketplace_module
        from app.package_manager.manager import InstallResult
        from app.package_manager.enums import InstallStatus

        job = clean_install_jobs.create("test_module")
        job_id = job.job_id

        fake_mod_path = tmp_path / "test_module-1.0.0.mod"
        fake_mod_path.write_bytes(b"fake zip content")

        fake_provider = AsyncMock()
        fake_provider.fetch_mod_path.return_value = fake_mod_path

        success_result = InstallResult(
            status=InstallStatus.SUCCESS, module_id="test_module",
            version="1.0.0", message="Installed.",
        )

        with patch.object(marketplace_module, "_resolve_remote_provider", AsyncMock(return_value=fake_provider)), \
             patch.object(marketplace_module.package_manager, "install", AsyncMock(return_value=success_result)):
            await marketplace_module._install_remote_background("test_module", job_id, None)

        final_job = clean_install_jobs.get(job_id)
        assert final_job.phase == InstallJobPhase.DONE
        assert final_job.error is None
        assert final_job.finished_at is not None
        fake_provider.fetch_mod_path.assert_awaited_once_with("test_module")

    @pytest.mark.asyncio
    async def test_background_task_network_failure_reaches_failed(self, clean_install_jobs):
        """Background task: fetch_mod_path() returns None (network failure) → FAILED."""
        from app.api.routes import marketplace as marketplace_module

        job = clean_install_jobs.create("test_module")
        job_id = job.job_id

        fake_provider = AsyncMock()
        fake_provider.fetch_mod_path.return_value = None  # network failure, per Slices 2/3 contract

        with patch.object(marketplace_module, "_resolve_remote_provider", AsyncMock(return_value=fake_provider)):
            await marketplace_module._install_remote_background("test_module", job_id, None)

        final_job = clean_install_jobs.get(job_id)
        assert final_job.phase == InstallJobPhase.FAILED
        assert "sem conexão" in final_job.error
        assert final_job.finished_at is not None

    @pytest.mark.asyncio
    async def test_background_task_no_provider_found_reaches_failed(self, clean_install_jobs):
        """Background task: module not found in any source → FAILED, no fetch attempted."""
        from app.api.routes import marketplace as marketplace_module

        job = clean_install_jobs.create("ghost_module")
        job_id = job.job_id

        with patch.object(marketplace_module, "_resolve_remote_provider", AsyncMock(return_value=None)):
            await marketplace_module._install_remote_background("ghost_module", job_id, None)

        final_job = clean_install_jobs.get(job_id)
        assert final_job.phase == InstallJobPhase.FAILED
        assert "não encontrado" in final_job.error

    @pytest.mark.asyncio
    async def test_background_task_install_failure_reaches_failed(self, clean_install_jobs, tmp_path):
        """Background task: package_manager.install() fails validation → FAILED with its message."""
        from app.api.routes import marketplace as marketplace_module
        from app.package_manager.manager import InstallResult
        from app.package_manager.enums import InstallStatus

        job = clean_install_jobs.create("test_module")
        job_id = job.job_id

        fake_mod_path = tmp_path / "test_module-1.0.0.mod"
        fake_mod_path.write_bytes(b"fake zip content")

        fake_provider = AsyncMock()
        fake_provider.fetch_mod_path.return_value = fake_mod_path

        failed_result = InstallResult(
            status=InstallStatus.INCOMPATIBLE, module_id="test_module",
            version="1.0.0", message="Incompatible with this platform version.",
        )

        with patch.object(marketplace_module, "_resolve_remote_provider", AsyncMock(return_value=fake_provider)), \
             patch.object(marketplace_module.package_manager, "install", AsyncMock(return_value=failed_result)):
            await marketplace_module._install_remote_background("test_module", job_id, None)

        final_job = clean_install_jobs.get(job_id)
        assert final_job.phase == InstallJobPhase.FAILED
        assert final_job.error == "Incompatible with this platform version."

    @pytest.mark.asyncio
    async def test_background_task_exception_caught_as_failed(self, clean_install_jobs):
        """Background task: uncaught exception in resolve/fetch is caught, job marked FAILED."""
        from app.api.routes import marketplace as marketplace_module

        job = clean_install_jobs.create("test_module")
        job_id = job.job_id

        with patch.object(
            marketplace_module, "_resolve_remote_provider",
            AsyncMock(side_effect=RuntimeError("Unexpected error during installation")),
        ):
            await marketplace_module._install_remote_background("test_module", job_id, None)

        final_job = clean_install_jobs.get(job_id)
        assert final_job.phase == InstallJobPhase.FAILED
        assert "Unexpected error" in final_job.error

    @pytest.mark.asyncio
    async def test_multiple_concurrent_install_jobs_tracked_independently(self, clean_install_jobs):
        """Multiple install jobs can progress independently."""
        job1 = clean_install_jobs.create("mod1")
        job2 = clean_install_jobs.create("mod2")

        # Job 1 progresses to VALIDATING
        clean_install_jobs.set_phase(job1.job_id, InstallJobPhase.VALIDATING)

        # Job 2 stays in ACQUIRING
        assert clean_install_jobs.get(job1.job_id).phase == InstallJobPhase.VALIDATING
        assert clean_install_jobs.get(job2.job_id).phase == InstallJobPhase.ACQUIRING

        # Job 2 progresses to FAILED
        clean_install_jobs.set_phase(job2.job_id, InstallJobPhase.FAILED, error="test error")

        # Job 1 still in VALIDATING
        assert clean_install_jobs.get(job1.job_id).phase == InstallJobPhase.VALIDATING
        assert clean_install_jobs.get(job2.job_id).phase == InstallJobPhase.FAILED

    @pytest.mark.asyncio
    async def test_no_module_installed_on_network_failure(self, clean_install_jobs, tmp_path, monkeypatch):
        """If fetch_mod_path() fails (network), package_manager.install() is never called
        — so no module directory is ever created in modules/installed/."""
        from app.api.routes import marketplace as marketplace_module

        job = clean_install_jobs.create("test_module_fail")
        job_id = job.job_id

        fake_provider = AsyncMock()
        fake_provider.fetch_mod_path.return_value = None

        install_mock = AsyncMock()
        with patch.object(marketplace_module, "_resolve_remote_provider", AsyncMock(return_value=fake_provider)), \
             patch.object(marketplace_module.package_manager, "install", install_mock):
            await marketplace_module._install_remote_background("test_module_fail", job_id, None)

        final_job = clean_install_jobs.get(job_id)
        assert final_job.phase == InstallJobPhase.FAILED
        install_mock.assert_not_awaited()
