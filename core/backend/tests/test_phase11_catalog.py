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
