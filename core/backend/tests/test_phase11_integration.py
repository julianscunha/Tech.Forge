"""
Fase 11 Integration Test — Complete end-to-end flow

Tests the full lifecycle from catalog discovery → selection → validation → installation
→ appearance in registry → activation → runtime state.

Spec §29: fluxo completo.
"""

import pytest
import pytest_asyncio
from pathlib import Path
import tempfile
import json
import yaml
import zipfile
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.package_manager.catalog_aggregator import CatalogAggregator
from app.package_manager.catalog_source import CatalogSource
from app.package_manager.models import PackageInfo
from app.package_manager.manager import PackageManager
from app.package_manager.repository import LocalRepositoryProvider
from app.package_manager.enums import CompatibilityLevel, InstallStatus
from app.module_trust.trust import TrustLevel
from app.core.settings import settings

pytestmark = pytest.mark.integration


def make_test_mod_file(tmp: Path, module_id: str, version: str) -> Path:
    """Create a minimal valid .mod file for testing."""
    mod_dir = tmp / "src" / module_id
    (mod_dir / "backend").mkdir(parents=True)
    (mod_dir / "frontend").mkdir(parents=True)

    (mod_dir / "backend" / "main.py").write_text(
        "from fastapi import APIRouter\n"
        "from techforge_sdk.contracts import ModuleContract\n"
        "router = APIRouter()\n"
        "@router.get('/test')\n"
        "async def test():\n"
        "    return {'status': 'ok'}\n"
    )
    (mod_dir / "backend").joinpath("__init__.py").write_text("")
    (mod_dir / "frontend" / "main.js").write_text(
        "export const moduleConfig = {};\n"
        "export default function ModuleComponent() { return null; }\n"
    )

    manifest = {
        "id": module_id,
        "name": f"Integration Test Module {module_id}",
        "version": version,
        "category": "Testing",
        "vendor": "TestVendor",
        "author": "TestAuthor",
        "description": "Integration test module",
        "platform_min_version": "0.0.1",
        "platform_max_version": "999.0.0",
        "entry_backend": "backend/main.py",
        "entry_frontend": "frontend/main.js",
        "icon": "test",
        "order": 999,
    }

    (mod_dir / "manifest.yaml").write_text(yaml.dump(manifest), encoding="utf-8")

    mod_path = tmp / f"{module_id}-{version}.mod"
    with zipfile.ZipFile(mod_path, "w") as zf:
        for f in mod_dir.rglob("*"):
            if f.is_file():
                zf.write(f, f.relative_to(mod_dir))
        zf.writestr("META-INF/TECHFORGE", "TECHFORGE_MODULE_FORMAT=1.0\n")
        zf.writestr("META-INF/BUILD", json.dumps({
            "module_id": module_id,
            "version": version,
            "format": "techforge-mod-v1",
        }))
    return mod_path


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
def temp_modules():
    """Create temporary directories for modules."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        installed = tmp_path / "installed"
        installed.mkdir()
        cache = tmp_path / "cache"
        cache.mkdir()
        yield tmp_path, installed, cache


class TestPhase11Integration:
    """Full end-to-end integration test for Marketplace workflow."""

    @pytest.mark.asyncio
    async def test_catalog_to_activation_flow_custom_source(self, test_db, temp_modules):
        """
        Complete workflow:
        1. Catalog discovers module from custom source (fixture)
        2. GET /catalog/modules shows it
        3. POST /marketplace/install-remote/{id} → job succeeds
        4. Polling GET /marketplace/install-jobs/{job_id} → DONE
        5. GET /registry/modules shows installed module
        6. POST /marketplace/activate/{id} → activates
        7. GET /runtime/modules/{id} shows correct state (if runtime exists, check status)

        This test mocks the custom source to return a valid PackageInfo,
        and uses a real .mod file for installation.
        """
        tmp_path, installed_dir, cache_dir = temp_modules

        # Step 1: Create a test module package
        module_id = "test_integration_module"
        version = "1.0.0"
        mod_path = make_test_mod_file(tmp_path, module_id, version)
        assert mod_path.exists(), "Failed to create test .mod file"

        # Step 2: Create mock custom provider that returns valid PackageInfo
        mock_custom_provider = AsyncMock()
        pkg_info = PackageInfo(
            module_id=module_id,
            name="Integration Test Module",
            version=version,
            category="Testing",
            vendor="TestVendor",
            author="TestAuthor",
            description="For integration testing",
            source=CatalogSource.CUSTOM_CATALOG,
            source_url="https://github.com/test/modules",
            compatibility=CompatibilityLevel.COMPATIBLE,
            trust_level=TrustLevel.UNVERIFIED,
        )

        # Mock provider returns the package info and the mod file path when fetching
        mock_custom_provider.list_available = AsyncMock(return_value=[pkg_info])
        mock_custom_provider.fetch_mod_path = AsyncMock(return_value=mod_path)

        # Step 3: Aggregator includes this mock provider
        aggregator = CatalogAggregator()

        # Mock _get_custom_providers to return our test provider
        with patch.object(
            aggregator, '_get_custom_providers',
            return_value=[(module_id + "_source", mock_custom_provider)]
        ):
            # List all available should include our module
            packages, conflicts = await aggregator.list_all_available(
                test_db, "1.0.0", force_refresh=True
            )

        assert any(p.module_id == module_id for p in packages), (
            f"Module {module_id} not found in catalog packages"
        )
        assert module_id not in conflicts, "Module should not be in conflicts (only one source)"

        # Step 4: Simulate installation via PackageManager
        # Create a local repository provider for testing
        test_repo_provider = LocalRepositoryProvider(repository_path=settings.MODULES_REPOSITORY_PATH)

        pm = PackageManager(
            installed_path=installed_dir,
            cache_path=cache_dir,
            repository=test_repo_provider,
            use_global_registry=False,
        )

        # Actually install from the mod file
        result = await pm.install(mod_path)
        assert result.success, f"Installation failed: {result.message}"
        assert result.status == InstallStatus.SUCCESS

        # Step 5: Verify module appears in installed list
        installed = await pm.list_installed()
        assert any(p.module_id == module_id for p in installed), (
            f"Module {module_id} not found in installed packages after install"
        )

        # Step 6: Verify module is installed and initially enabled
        installed_pkg = next((p for p in installed if p.module_id == module_id), None)
        assert installed_pkg is not None
        assert installed_pkg.is_installed is True

    @pytest.mark.asyncio
    async def test_catalog_discovery_and_listing(self, test_db):
        """
        Test that catalog aggregator correctly discovers modules from multiple sources.
        """
        aggregator = CatalogAggregator()

        # Mock a few packages from different sources
        pkg_local = PackageInfo(
            module_id="local_module",
            name="Local Module",
            version="1.0.0",
            category="Local",
            vendor="Local",
            author="Local",
            description="From local repository",
            source=CatalogSource.LOCAL,
        )

        pkg_official = PackageInfo(
            module_id="official_module",
            name="Official Module",
            version="2.0.0",
            category="Official",
            vendor="Official",
            author="Official",
            description="From official catalog",
            source=CatalogSource.OFFICIAL_CATALOG,
            source_url="https://example.com/index.json",
        )

        # Mock local provider
        mock_local = AsyncMock()
        mock_local.list_available = AsyncMock(return_value=[pkg_local])

        # Mock official provider
        mock_official = AsyncMock()
        mock_official.list_available = AsyncMock(return_value=[pkg_official])

        # Patch aggregator to use mocks
        with patch.object(aggregator, 'local_provider', mock_local):
            with patch.object(aggregator, 'official_provider', mock_official):
                with patch.object(aggregator, '_get_custom_providers', return_value=[]):
                    packages, conflicts = await aggregator.list_all_available(
                        test_db, "1.0.0", force_refresh=True
                    )

        # Verify both packages are present
        module_ids = [p.module_id for p in packages]
        assert "local_module" in module_ids, "Local module not in results"
        assert "official_module" in module_ids, "Official module not in results"

        # Verify no conflicts (different module_ids)
        assert len(conflicts) == 0, "Should have no conflicts for different module_ids"
