"""
Fase 11 Slice 1: CatalogSource enum + PackageInfo.source/source_url + detect_conflicts

Tests for catalog source tracking and conflict detection.
"""

import pytest
from app.package_manager.catalog_source import CatalogSource
from app.package_manager.conflicts import detect_conflicts
from app.package_manager.models import PackageInfo
from app.package_manager.enums import CompatibilityLevel
from app.module_trust.trust import TrustLevel


class TestCatalogSource:
    """Test CatalogSource enum values."""

    def test_catalog_source_has_local(self):
        assert CatalogSource.LOCAL.value == "local"

    def test_catalog_source_has_official_catalog(self):
        assert CatalogSource.OFFICIAL_CATALOG.value == "official_catalog"

    def test_catalog_source_has_custom_catalog(self):
        assert CatalogSource.CUSTOM_CATALOG.value == "custom_catalog"


class TestPackageInfoSource:
    """Test PackageInfo source and source_url fields."""

    def test_package_info_defaults_to_local_source(self):
        """PackageInfo without explicit source should default to LOCAL."""
        pkg = PackageInfo(
            module_id="test_module",
            name="Test Module",
            version="1.0.0",
            category="Testing",
            vendor="TestVendor",
            author="TestAuthor",
            description="A test module",
        )
        assert pkg.source == CatalogSource.LOCAL
        assert pkg.source_url is None

    def test_package_info_with_official_catalog_source(self):
        """PackageInfo can be created with OFFICIAL_CATALOG source."""
        pkg = PackageInfo(
            module_id="official_module",
            name="Official Module",
            version="2.0.0",
            category="Official",
            vendor="OfficialVendor",
            author="OfficialAuthor",
            description="From official catalog",
            source=CatalogSource.OFFICIAL_CATALOG,
            source_url="https://example.com/index.json",
        )
        assert pkg.source == CatalogSource.OFFICIAL_CATALOG
        assert pkg.source_url == "https://example.com/index.json"

    def test_package_info_with_custom_catalog_source(self):
        """PackageInfo can be created with CUSTOM_CATALOG source."""
        pkg = PackageInfo(
            module_id="custom_module",
            name="Custom Module",
            version="1.5.0",
            category="Custom",
            vendor="CustomVendor",
            author="CustomAuthor",
            description="From custom catalog",
            source=CatalogSource.CUSTOM_CATALOG,
            source_url="https://github.com/user/repo",
        )
        assert pkg.source == CatalogSource.CUSTOM_CATALOG
        assert pkg.source_url == "https://github.com/user/repo"

    def test_package_info_preserves_backwards_compatibility(self):
        """Existing code creating PackageInfo without source should work unchanged."""
        # This mimics code from Fase 4, 8.1, 9, 10 that creates PackageInfo
        # without knowing about source/source_url
        pkg = PackageInfo(
            module_id="legacy_module",
            name="Legacy Module",
            version="1.0.0",
            category="Legacy",
            vendor="LegacyVendor",
            author="LegacyAuthor",
            description="Created without source field",
            compatibility=CompatibilityLevel.COMPATIBLE,
            trust_level=TrustLevel.UNVERIFIED,
        )
        # Should have defaults
        assert pkg.source == CatalogSource.LOCAL
        assert pkg.source_url is None
        # Everything else should work as before
        assert pkg.module_id == "legacy_module"
        assert pkg.is_compatible is True


class TestDetectConflicts:
    """Test detect_conflicts function for identifying modules in multiple sources."""

    def test_detect_conflicts_empty_list(self):
        """Empty list of packages should return empty dict."""
        result = detect_conflicts([])
        assert result == {}

    def test_detect_conflicts_single_package(self):
        """Single package should not be in conflicts."""
        pkg = PackageInfo(
            module_id="single_module",
            name="Single",
            version="1.0.0",
            category="Test",
            vendor="Vendor",
            author="Author",
            description="Single package",
        )
        result = detect_conflicts([pkg])
        assert result == {}

    def test_detect_conflicts_same_module_different_sources(self):
        """Same module_id in different sources should be detected as conflict."""
        pkg_local = PackageInfo(
            module_id="shared_module",
            name="Shared Module",
            version="1.0.0",
            category="Test",
            vendor="Vendor",
            author="Author",
            description="From local",
            source=CatalogSource.LOCAL,
        )
        pkg_official = PackageInfo(
            module_id="shared_module",
            name="Shared Module",
            version="2.0.0",
            category="Test",
            vendor="OfficialVendor",
            author="OfficialAuthor",
            description="From official catalog",
            source=CatalogSource.OFFICIAL_CATALOG,
            source_url="https://example.com/index.json",
        )
        result = detect_conflicts([pkg_local, pkg_official])
        assert "shared_module" in result
        assert len(result["shared_module"]) == 2
        assert pkg_local in result["shared_module"]
        assert pkg_official in result["shared_module"]

    def test_detect_conflicts_same_module_same_source_no_conflict(self):
        """Same module_id in same source should NOT be a conflict."""
        pkg1 = PackageInfo(
            module_id="same_source_module",
            name="Module V1",
            version="1.0.0",
            category="Test",
            vendor="Vendor",
            author="Author",
            description="Version 1",
            source=CatalogSource.LOCAL,
        )
        pkg2 = PackageInfo(
            module_id="same_source_module",
            name="Module V1",
            version="1.0.0",
            category="Test",
            vendor="Vendor",
            author="Author",
            description="Version 1 (duplicate in same source)",
            source=CatalogSource.LOCAL,
        )
        result = detect_conflicts([pkg1, pkg2])
        # Same source = not a conflict, should not appear
        assert result == {}

    def test_detect_conflicts_different_modules_different_sources(self):
        """Different module_ids should not be in conflicts."""
        pkg1 = PackageInfo(
            module_id="module_a",
            name="Module A",
            version="1.0.0",
            category="Test",
            vendor="Vendor",
            author="Author",
            description="Module A",
            source=CatalogSource.LOCAL,
        )
        pkg2 = PackageInfo(
            module_id="module_b",
            name="Module B",
            version="2.0.0",
            category="Test",
            vendor="Vendor",
            author="Author",
            description="Module B",
            source=CatalogSource.OFFICIAL_CATALOG,
        )
        result = detect_conflicts([pkg1, pkg2])
        assert result == {}

    def test_detect_conflicts_three_sources_one_module(self):
        """Same module_id in 3 different sources should be detected."""
        pkg_local = PackageInfo(
            module_id="multi_source",
            name="Multi Source",
            version="1.0.0",
            category="Test",
            vendor="Local",
            author="Author",
            description="Local version",
            source=CatalogSource.LOCAL,
        )
        pkg_official = PackageInfo(
            module_id="multi_source",
            name="Multi Source",
            version="2.0.0",
            category="Test",
            vendor="Official",
            author="Author",
            description="Official version",
            source=CatalogSource.OFFICIAL_CATALOG,
            source_url="https://official.example.com",
        )
        pkg_custom = PackageInfo(
            module_id="multi_source",
            name="Multi Source",
            version="3.0.0",
            category="Test",
            vendor="Custom",
            author="Author",
            description="Custom version",
            source=CatalogSource.CUSTOM_CATALOG,
            source_url="https://github.com/custom/repo",
        )
        result = detect_conflicts([pkg_local, pkg_official, pkg_custom])
        assert "multi_source" in result
        assert len(result["multi_source"]) == 3

    def test_detect_conflicts_multiple_conflicts(self):
        """Multiple different modules with conflicts should all appear."""
        # Module X in 2 sources
        pkg_x_local = PackageInfo(
            module_id="module_x",
            name="Module X",
            version="1.0.0",
            category="Test",
            vendor="Vendor",
            author="Author",
            description="X local",
            source=CatalogSource.LOCAL,
        )
        pkg_x_official = PackageInfo(
            module_id="module_x",
            name="Module X",
            version="2.0.0",
            category="Test",
            vendor="Vendor",
            author="Author",
            description="X official",
            source=CatalogSource.OFFICIAL_CATALOG,
        )
        # Module Y in 2 sources
        pkg_y_local = PackageInfo(
            module_id="module_y",
            name="Module Y",
            version="1.0.0",
            category="Test",
            vendor="Vendor",
            author="Author",
            description="Y local",
            source=CatalogSource.LOCAL,
        )
        pkg_y_custom = PackageInfo(
            module_id="module_y",
            name="Module Y",
            version="3.0.0",
            category="Test",
            vendor="Vendor",
            author="Author",
            description="Y custom",
            source=CatalogSource.CUSTOM_CATALOG,
        )
        # Module Z in 1 source (no conflict)
        pkg_z = PackageInfo(
            module_id="module_z",
            name="Module Z",
            version="1.0.0",
            category="Test",
            vendor="Vendor",
            author="Author",
            description="Z",
            source=CatalogSource.OFFICIAL_CATALOG,
        )

        result = detect_conflicts([
            pkg_x_local, pkg_x_official,
            pkg_y_local, pkg_y_custom,
            pkg_z,
        ])

        assert set(result.keys()) == {"module_x", "module_y"}
        assert len(result["module_x"]) == 2
        assert len(result["module_y"]) == 2


# ── Tests for Slice 2: OfficialCatalogProvider ────────────────────────────────

class TestOfficialCatalogProvider:
    """Test OfficialCatalogProvider for fetching from index.json."""

    @pytest.mark.asyncio
    async def test_list_available_parses_index_json(self, tmp_path):
        """OfficialCatalogProvider.list_available() fetches and parses index.json."""
        from unittest.mock import AsyncMock, patch, MagicMock
        from app.package_manager.repository import OfficialCatalogProvider

        # Mock index.json response
        index_data = {
            "modules": [
                {
                    "id": "module_a",
                    "name": "Module A",
                    "version": "1.0.0",
                    "category": "Utilities",
                    "vendor": "VendorA",
                    "author": "AuthorA",
                    "description": "Module A description",
                    "mod_url": "module_a-1.0.0.mod",
                    "checksum": "abc123",
                },
                {
                    "id": "module_b",
                    "name": "Module B",
                    "version": "2.0.0",
                    "category": "Tools",
                    "vendor": "VendorB",
                    "author": "AuthorB",
                    "description": "Module B description",
                    "mod_url": "module_b-2.0.0.mod",
                    "checksum": "def456",
                },
            ]
        }

        provider = OfficialCatalogProvider(
            base_url="https://example.com/catalog",
            cache_path=tmp_path,
        )

        # Mock httpx.AsyncClient
        mock_response = MagicMock()
        mock_response.json.return_value = index_data
        mock_response.status_code = 200

        async def mock_get(*args, **kwargs):
            return mock_response

        mock_client = MagicMock()
        mock_client.get = mock_get
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            packages = await provider.list_available("1.0.0")

        assert len(packages) == 2
        assert packages[0].module_id == "module_a"
        assert packages[0].name == "Module A"
        assert packages[0].source == CatalogSource.OFFICIAL_CATALOG
        assert packages[0].source_url == "module_a-1.0.0.mod"
        assert packages[1].module_id == "module_b"

    @pytest.mark.asyncio
    async def test_list_available_network_error_returns_empty_list(self, tmp_path):
        """OfficialCatalogProvider returns [] on network error, doesn't raise."""
        from unittest.mock import AsyncMock, patch, MagicMock
        from app.package_manager.repository import OfficialCatalogProvider
        import httpx

        provider = OfficialCatalogProvider(
            base_url="https://example.com/catalog",
            cache_path=tmp_path,
        )

        # Mock httpx.AsyncClient to raise ConnectError
        async def mock_get(*args, **kwargs):
            raise httpx.ConnectError("Connection failed")

        mock_client = MagicMock()
        mock_client.get = mock_get
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            packages = await provider.list_available("1.0.0")

        assert packages == []

    @pytest.mark.asyncio
    async def test_list_available_http_error_returns_empty_list(self, tmp_path):
        """OfficialCatalogProvider returns [] on HTTP error (e.g., 404, 500)."""
        from unittest.mock import AsyncMock, patch, MagicMock
        from app.package_manager.repository import OfficialCatalogProvider

        provider = OfficialCatalogProvider(
            base_url="https://example.com/catalog",
            cache_path=tmp_path,
        )

        # Mock response with 404 status
        mock_response = MagicMock()
        mock_response.status_code = 404

        async def mock_get(*args, **kwargs):
            return mock_response

        mock_client = MagicMock()
        mock_client.get = mock_get
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            packages = await provider.list_available("1.0.0")

        assert packages == []

    @pytest.mark.asyncio
    async def test_get_package_filters_by_id(self, tmp_path):
        """OfficialCatalogProvider.get_package() returns matching module or None."""
        from unittest.mock import AsyncMock, patch, MagicMock
        from app.package_manager.repository import OfficialCatalogProvider

        index_data = {
            "modules": [
                {
                    "id": "target_module",
                    "name": "Target Module",
                    "version": "1.0.0",
                    "category": "Test",
                    "vendor": "Vendor",
                    "author": "Author",
                    "description": "Target",
                    "mod_url": "target_module-1.0.0.mod",
                    "checksum": "abc123",
                },
                {
                    "id": "other_module",
                    "name": "Other Module",
                    "version": "1.0.0",
                    "category": "Test",
                    "vendor": "Vendor",
                    "author": "Author",
                    "description": "Other",
                    "mod_url": "other_module-1.0.0.mod",
                    "checksum": "def456",
                },
            ]
        }

        provider = OfficialCatalogProvider(
            base_url="https://example.com/catalog",
            cache_path=tmp_path,
        )

        mock_response = MagicMock()
        mock_response.json.return_value = index_data
        mock_response.status_code = 200

        async def mock_get(*args, **kwargs):
            return mock_response

        mock_client = MagicMock()
        mock_client.get = mock_get
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            pkg = await provider.get_package("target_module", "1.0.0")

        assert pkg is not None
        assert pkg.module_id == "target_module"

        # Non-existent module returns None
        with patch("httpx.AsyncClient", return_value=mock_client):
            pkg = await provider.get_package("nonexistent_module", "1.0.0")

        assert pkg is None

    @pytest.mark.asyncio
    async def test_fetch_mod_path_downloads_and_caches(self, tmp_path):
        """OfficialCatalogProvider.fetch_mod_path() downloads .mod to cache."""
        from unittest.mock import AsyncMock, patch, MagicMock
        from app.package_manager.repository import OfficialCatalogProvider

        index_data = {
            "modules": [
                {
                    "id": "download_module",
                    "name": "Download Module",
                    "version": "1.0.0",
                    "category": "Test",
                    "vendor": "Vendor",
                    "author": "Author",
                    "description": "For download",
                    "mod_url": "https://example.com/download_module-1.0.0.mod",
                    "checksum": "abc123",
                },
            ]
        }

        provider = OfficialCatalogProvider(
            base_url="https://example.com/catalog",
            cache_path=tmp_path,
        )

        # Mock the GET for index.json
        index_response = MagicMock()
        index_response.json.return_value = index_data
        index_response.status_code = 200

        # Mock the GET for the .mod file
        mod_content = b"mock .mod content"
        mod_response = MagicMock()
        mod_response.content = mod_content
        mod_response.status_code = 200

        # Create responses for each call
        responses = [index_response, mod_response]
        response_iter = iter(responses)

        async def mock_get(*args, **kwargs):
            return next(response_iter)

        mock_client = MagicMock()
        mock_client.get = mock_get
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await provider.fetch_mod_path("download_module")

        assert result is not None
        assert result.exists()
        assert result.read_bytes() == mod_content
