"""
Fase 11 Slice 4: CatalogSourceConfig + Cache com TTL + Agregador + Invalidação

Tests for catalog source configuration, in-memory cache with TTL, and
multi-source aggregation without breaking other sources on failure.
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import asyncio

from app.db.database import Base
from app.models.catalog_source import CatalogSourceConfig
from app.models.catalog_favorite import CatalogFavorite
from app.services.catalog_source import CatalogSourceService
from app.services.catalog_favorite import CatalogFavoriteService
from app.package_manager.catalog_cache import CatalogCache
from app.package_manager.catalog_aggregator import CatalogAggregator
from app.package_manager.catalog_source import CatalogSource
from app.package_manager.models import PackageInfo
from app.package_manager.enums import CompatibilityLevel
from app.module_trust.trust import TrustLevel


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
def fresh_cache():
    """Create a fresh cache instance for each test."""
    return CatalogCache(ttl_seconds=60)


# ──────────────────────────────────────────────────────────────────────────────
# Part A — CatalogSourceConfig CRUD
# ──────────────────────────────────────────────────────────────────────────────

class TestCatalogSourceConfigCRUD:
    """Test CatalogSourceConfig table operations."""

    @pytest.mark.asyncio
    async def test_add_custom_catalog_source(self, test_db):
        """Add a custom catalog source to the database."""
        source = await CatalogSourceService.add(
            test_db,
            name="My Modules",
            url="https://github.com/user/modules",
            source_type=CatalogSource.CUSTOM_CATALOG,
        )

        assert source.id is not None
        assert source.name == "My Modules"
        assert source.url == "https://github.com/user/modules"
        assert source.type == CatalogSource.CUSTOM_CATALOG.value
        assert source.enabled is True
        assert isinstance(source.created_at, datetime)

    @pytest.mark.asyncio
    async def test_add_official_catalog_source(self, test_db):
        """Add an official catalog source (usually read-only, but test the table)."""
        source = await CatalogSourceService.add(
            test_db,
            name="Tech.Forge Official",
            url="https://techforge.io/catalog/index.json",
            source_type=CatalogSource.OFFICIAL_CATALOG,
        )

        assert source.type == CatalogSource.OFFICIAL_CATALOG.value
        assert source.enabled is True

    @pytest.mark.asyncio
    async def test_list_all_sources(self, test_db):
        """List all catalog sources (should be empty initially, then have 2)."""
        # Initially empty
        sources = await CatalogSourceService.list_all(test_db)
        assert len(sources) == 0

        # Add two sources
        await CatalogSourceService.add(test_db, "First", "https://first.com", CatalogSource.CUSTOM_CATALOG)
        await CatalogSourceService.add(test_db, "Second", "https://second.com", CatalogSource.CUSTOM_CATALOG)

        sources = await CatalogSourceService.list_all(test_db)
        assert len(sources) == 2
        assert sources[0].name == "First"
        assert sources[1].name == "Second"

    @pytest.mark.asyncio
    async def test_remove_source(self, test_db):
        """Remove a catalog source by id."""
        source = await CatalogSourceService.add(
            test_db, "To Remove", "https://remove.me", CatalogSource.CUSTOM_CATALOG
        )
        source_id = source.id

        # Verify it exists
        sources_before = await CatalogSourceService.list_all(test_db)
        assert len(sources_before) == 1

        # Remove it
        removed = await CatalogSourceService.remove(test_db, source_id)
        assert removed is True

        # Verify it's gone
        sources_after = await CatalogSourceService.list_all(test_db)
        assert len(sources_after) == 0

    @pytest.mark.asyncio
    async def test_remove_nonexistent_source(self, test_db):
        """Removing a non-existent source returns False."""
        result = await CatalogSourceService.remove(test_db, "nonexistent-id")
        assert result is False

    @pytest.mark.asyncio
    async def test_toggle_source_enabled(self, test_db):
        """Toggle a source's enabled status."""
        source = await CatalogSourceService.add(
            test_db, "Test", "https://test.com", CatalogSource.CUSTOM_CATALOG
        )
        source_id = source.id

        # Initially enabled
        assert source.enabled is True

        # Disable it
        disabled = await CatalogSourceService.toggle(test_db, source_id, False)
        assert disabled is not None
        assert disabled.enabled is False

        # Re-enable it
        enabled = await CatalogSourceService.toggle(test_db, source_id, True)
        assert enabled is not None
        assert enabled.enabled is True

    @pytest.mark.asyncio
    async def test_toggle_nonexistent_source(self, test_db):
        """Toggling a non-existent source returns None."""
        result = await CatalogSourceService.toggle(test_db, "nonexistent-id", False)
        assert result is None

    @pytest.mark.asyncio
    async def test_multiple_custom_sources_simultaneously(self, test_db):
        """Multiple custom sources can coexist without limit."""
        names = ["Backup", "Storage", "Analytics", "Security"]

        for name in names:
            await CatalogSourceService.add(
                test_db,
                name=name,
                url=f"https://github.com/org/{name.lower()}",
                source_type=CatalogSource.CUSTOM_CATALOG,
            )

        sources = await CatalogSourceService.list_all(test_db)
        assert len(sources) == 4
        assert [s.name for s in sources] == names


# ──────────────────────────────────────────────────────────────────────────────
# Part B — Cache with TTL
# ──────────────────────────────────────────────────────────────────────────────

class TestCatalogCache:
    """Test in-memory cache with TTL per source."""

    def test_cache_get_miss_when_empty(self):
        """get() returns None when cache is empty."""
        cache = CatalogCache(ttl_seconds=60)
        result = cache.get("source-1")
        assert result is None

    def test_cache_set_and_get(self):
        """set() stores packages, get() retrieves them."""
        cache = CatalogCache(ttl_seconds=60)

        pkg = PackageInfo(
            module_id="test_mod",
            name="Test Module",
            version="1.0.0",
            category="Test",
            vendor="TestVendor",
            author="TestAuthor",
            description="Test",
        )

        cache.set("source-1", [pkg])
        result = cache.get("source-1")

        assert result is not None
        assert len(result) == 1
        assert result[0].module_id == "test_mod"

    def test_cache_get_returns_none_after_ttl_expires(self):
        """get() returns None after TTL expires."""
        cache = CatalogCache(ttl_seconds=1)

        pkg = PackageInfo(
            module_id="test_mod",
            name="Test Module",
            version="1.0.0",
            category="Test",
            vendor="TestVendor",
            author="TestAuthor",
            description="Test",
        )

        cache.set("source-1", [pkg])

        # Mock time passage by directly manipulating the cache's internal timestamp
        cache._cache["source-1"]["fetched_at"] = datetime.now() - timedelta(seconds=2)

        result = cache.get("source-1")
        assert result is None

    def test_cache_invalidate(self):
        """invalidate() removes an entry immediately."""
        cache = CatalogCache(ttl_seconds=3600)

        pkg = PackageInfo(
            module_id="test_mod",
            name="Test Module",
            version="1.0.0",
            category="Test",
            vendor="TestVendor",
            author="TestAuthor",
            description="Test",
        )

        cache.set("source-1", [pkg])
        assert cache.get("source-1") is not None

        cache.invalidate("source-1")
        assert cache.get("source-1") is None

    def test_cache_separate_entries_per_source(self):
        """Different sources have separate cache entries."""
        cache = CatalogCache(ttl_seconds=60)

        pkg1 = PackageInfo(
            module_id="mod1",
            name="Mod 1",
            version="1.0.0",
            category="Test",
            vendor="V1",
            author="A1",
            description="Test 1",
        )

        pkg2 = PackageInfo(
            module_id="mod2",
            name="Mod 2",
            version="2.0.0",
            category="Test",
            vendor="V2",
            author="A2",
            description="Test 2",
        )

        cache.set("source-1", [pkg1])
        cache.set("source-2", [pkg2])

        result1 = cache.get("source-1")
        result2 = cache.get("source-2")

        assert result1[0].module_id == "mod1"
        assert result2[0].module_id == "mod2"


# ──────────────────────────────────────────────────────────────────────────────
# Part B — CatalogAggregator
# ──────────────────────────────────────────────────────────────────────────────

class TestCatalogAggregator:
    """Test multi-source aggregation with cache and conflict detection."""

    @pytest.mark.asyncio
    async def test_aggregator_lists_all_available_sources(self, test_db, fresh_cache):
        """list_all_available() returns packages from all enabled sources."""
        # Setup: Create sources in DB
        source1 = await CatalogSourceService.add(
            test_db, "Source 1", "https://source1.com", CatalogSource.CUSTOM_CATALOG
        )

        # Create mock providers
        pkg1 = PackageInfo(
            module_id="pkg1",
            name="Package 1",
            version="1.0.0",
            category="Test",
            vendor="V1",
            author="A1",
            description="Test 1",
            source=CatalogSource.LOCAL,
        )

        pkg2 = PackageInfo(
            module_id="pkg2",
            name="Package 2",
            version="2.0.0",
            category="Test",
            vendor="V2",
            author="A2",
            description="Test 2",
            source=CatalogSource.CUSTOM_CATALOG,
            source_url="https://source1.com",
        )

        # Create aggregator with mocked providers
        aggregator = CatalogAggregator(cache=fresh_cache)

        # Mock the local provider
        local_provider = AsyncMock()
        local_provider.list_available.return_value = [pkg1]

        # Mock the official provider
        official_provider = AsyncMock()
        official_provider.list_available.return_value = []

        # Mock the custom provider
        custom_provider = AsyncMock()
        custom_provider.list_available.return_value = [pkg2]

        async def mock_get_custom_providers(db):
            return [("source-1", custom_provider)]

        with patch.object(aggregator, 'local_provider', local_provider):
            with patch.object(aggregator, 'official_provider', official_provider):
                with patch.object(aggregator, '_get_custom_providers', side_effect=mock_get_custom_providers):
                    packages, conflicts = await aggregator.list_all_available(test_db, "1.0.0")

        # Should have both packages
        assert len(packages) == 2
        assert packages[0].module_id == "pkg1"
        assert packages[1].module_id == "pkg2"
        # No conflicts (different module_ids)
        assert len(conflicts) == 0

    @pytest.mark.asyncio
    async def test_aggregator_respects_cache_ttl(self, test_db, fresh_cache):
        """Two calls within TTL use cache; call count reflects this."""
        pkg = PackageInfo(
            module_id="pkg1",
            name="Package 1",
            version="1.0.0",
            category="Test",
            vendor="V1",
            author="A1",
            description="Test 1",
            source=CatalogSource.LOCAL,
        )

        aggregator = CatalogAggregator(cache=fresh_cache)

        # Mock all providers
        local_provider = AsyncMock()
        local_provider.list_available.return_value = [pkg]

        official_provider = AsyncMock()
        official_provider.list_available.return_value = []

        with patch.object(aggregator, 'local_provider', local_provider):
            with patch.object(aggregator, 'official_provider', official_provider):
                with patch.object(aggregator, '_get_custom_providers', return_value=[]):
                    # First call
                    packages1, _ = await aggregator.list_all_available(test_db, "1.0.0")
                    assert len(packages1) == 1

                    # Second call within TTL
                    packages2, _ = await aggregator.list_all_available(test_db, "1.0.0")
                    assert len(packages2) == 1

                    # Verify local provider was called only once (cache hit on second call)
                    assert local_provider.list_available.call_count == 1

    @pytest.mark.asyncio
    async def test_aggregator_force_refresh_ignores_cache(self, test_db, fresh_cache):
        """force_refresh=True calls providers even within TTL."""
        pkg = PackageInfo(
            module_id="pkg1",
            name="Package 1",
            version="1.0.0",
            category="Test",
            vendor="V1",
            author="A1",
            description="Test 1",
            source=CatalogSource.LOCAL,
        )

        aggregator = CatalogAggregator(cache=fresh_cache)

        # Mock all providers
        local_provider = AsyncMock()
        local_provider.list_available.return_value = [pkg]

        official_provider = AsyncMock()
        official_provider.list_available.return_value = []

        with patch.object(aggregator, 'local_provider', local_provider):
            with patch.object(aggregator, 'official_provider', official_provider):
                with patch.object(aggregator, '_get_custom_providers', return_value=[]):
                    # First call
                    await aggregator.list_all_available(test_db, "1.0.0")

                    # Second call with force_refresh=True
                    await aggregator.list_all_available(test_db, "1.0.0", force_refresh=True)

                    # Both calls should have hit the provider
                    assert local_provider.list_available.call_count == 2

    @pytest.mark.asyncio
    async def test_aggregator_one_failing_source_doesnt_break_others(self, test_db, fresh_cache):
        """When one source raises an exception, others still return results."""
        pkg_good = PackageInfo(
            module_id="good_pkg",
            name="Good Package",
            version="1.0.0",
            category="Test",
            vendor="V1",
            author="A1",
            description="Good",
            source=CatalogSource.LOCAL,
        )

        aggregator = CatalogAggregator(cache=fresh_cache)

        # Local provider works fine
        local_provider = AsyncMock()
        local_provider.list_available.return_value = [pkg_good]

        # Official provider raises an exception
        official_provider = AsyncMock()
        official_provider.list_available.side_effect = Exception("Network error")

        with patch.object(aggregator, 'local_provider', local_provider):
            with patch.object(aggregator, 'official_provider', official_provider):
                with patch.object(aggregator, '_get_custom_providers', return_value=[]):
                    # Should not raise; just return what it got from local
                    packages, _ = await aggregator.list_all_available(test_db, "1.0.0")
                    assert len(packages) == 1
                    assert packages[0].module_id == "good_pkg"

    @pytest.mark.asyncio
    async def test_aggregator_detects_conflicts(self, test_db, fresh_cache):
        """Same module_id from different sources appears in conflicts."""
        pkg_local = PackageInfo(
            module_id="shared_mod",
            name="Shared Module",
            version="1.0.0",
            category="Test",
            vendor="V1",
            author="A1",
            description="Local",
            source=CatalogSource.LOCAL,
        )

        pkg_official = PackageInfo(
            module_id="shared_mod",
            name="Shared Module",
            version="1.1.0",
            category="Test",
            vendor="V1",
            author="A1",
            description="Official",
            source=CatalogSource.OFFICIAL_CATALOG,
            source_url="https://techforge.io/index.json",
        )

        aggregator = CatalogAggregator(cache=fresh_cache)

        # Mock providers
        local_provider = AsyncMock()
        local_provider.list_available.return_value = [pkg_local]

        official_provider = AsyncMock()
        official_provider.list_available.return_value = [pkg_official]

        with patch.object(aggregator, 'local_provider', local_provider):
            with patch.object(aggregator, 'official_provider', official_provider):
                with patch.object(aggregator, '_get_custom_providers', return_value=[]):
                    packages, conflicts = await aggregator.list_all_available(test_db, "1.0.0")

        # Both packages should be in the list
        assert len(packages) == 2

        # Conflict should be detected
        assert "shared_mod" in conflicts
        assert len(conflicts["shared_mod"]) == 2


# ──────────────────────────────────────────────────────────────────────────────
# Part C — Cache Invalidation in CRUD
# ──────────────────────────────────────────────────────────────────────────────

class TestCatalogSourceCacheInvalidation:
    """Test that CRUD operations invalidate cache appropriately."""

    @pytest.mark.asyncio
    async def test_update_url_invalidates_cache(self, test_db):
        """Editing a source's URL invalidates its cache entry."""
        # Add a source
        source = await CatalogSourceService.add(
            test_db,
            name="Test Source",
            url="https://old.url.com",
            source_type=CatalogSource.CUSTOM_CATALOG,
        )
        source_id = source.id

        # Cache some data for this source
        cache = CatalogCache(ttl_seconds=3600)
        pkg = PackageInfo(
            module_id="pkg1",
            name="Pkg 1",
            version="1.0.0",
            category="Test",
            vendor="V",
            author="A",
            description="Test",
        )
        cache.set(source_id, [pkg])

        # Verify cache has data
        assert cache.get(source_id) is not None

        # Update the URL (this should invalidate cache)
        updated = await CatalogSourceService.update_url(
            test_db, source_id, "https://new.url.com", cache
        )

        # Verify the URL was updated
        assert updated.url == "https://new.url.com"

        # Verify cache was invalidated
        assert cache.get(source_id) is None

    @pytest.mark.asyncio
    async def test_remove_source_invalidates_cache(self, test_db):
        """Removing a source invalidates its cache entry."""
        # Add a source
        source = await CatalogSourceService.add(
            test_db,
            name="Test Source",
            url="https://test.url.com",
            source_type=CatalogSource.CUSTOM_CATALOG,
        )
        source_id = source.id

        # Cache some data
        cache = CatalogCache(ttl_seconds=3600)
        pkg = PackageInfo(
            module_id="pkg1",
            name="Pkg 1",
            version="1.0.0",
            category="Test",
            vendor="V",
            author="A",
            description="Test",
        )
        cache.set(source_id, [pkg])

        # Verify cache has data
        assert cache.get(source_id) is not None

        # Remove the source (should invalidate cache)
        removed = await CatalogSourceService.remove(test_db, source_id, cache)

        # Verify source is gone
        assert removed is True

        # Verify cache was invalidated
        assert cache.get(source_id) is None


# ──────────────────────────────────────────────────────────────────────────────
# Part D — CatalogFavorite (Slice 4.5)
# ──────────────────────────────────────────────────────────────────────────────

class TestCatalogFavorite:
    """Test catalog favorites (local, no public ratings)."""

    @pytest.mark.asyncio
    async def test_add_favorite(self, test_db):
        """Add a module to favorites."""
        from app.models.catalog_favorite import CatalogFavorite
        from app.services.catalog_favorite import CatalogFavoriteService

        favorite = await CatalogFavoriteService.add(test_db, "test_module_1")

        assert favorite.module_id == "test_module_1"
        assert isinstance(favorite.favorited_at, datetime)

    @pytest.mark.asyncio
    async def test_add_favorite_idempotent(self, test_db):
        """Adding the same favorite twice does not create duplicates."""
        from app.services.catalog_favorite import CatalogFavoriteService

        fav1 = await CatalogFavoriteService.add(test_db, "test_module_1")
        fav2 = await CatalogFavoriteService.add(test_db, "test_module_1")

        # Should return the same favorite (same favorited_at timestamp)
        assert fav1.module_id == fav2.module_id
        assert fav1.favorited_at == fav2.favorited_at

        # Verify only one entry exists in DB
        favorites = await CatalogFavoriteService.list_ids(test_db)
        assert favorites == {"test_module_1"}

    @pytest.mark.asyncio
    async def test_list_favorites(self, test_db):
        """List all favorited module IDs."""
        from app.services.catalog_favorite import CatalogFavoriteService

        # Initially empty
        favorites = await CatalogFavoriteService.list_ids(test_db)
        assert favorites == set()

        # Add two favorites
        await CatalogFavoriteService.add(test_db, "mod_1")
        await CatalogFavoriteService.add(test_db, "mod_2")

        favorites = await CatalogFavoriteService.list_ids(test_db)
        assert favorites == {"mod_1", "mod_2"}

    @pytest.mark.asyncio
    async def test_remove_favorite(self, test_db):
        """Remove a favorite by module_id."""
        from app.services.catalog_favorite import CatalogFavoriteService

        await CatalogFavoriteService.add(test_db, "mod_to_remove")

        # Verify it exists
        favorites_before = await CatalogFavoriteService.list_ids(test_db)
        assert "mod_to_remove" in favorites_before

        # Remove it
        removed = await CatalogFavoriteService.remove(test_db, "mod_to_remove")
        assert removed is True

        # Verify it's gone
        favorites_after = await CatalogFavoriteService.list_ids(test_db)
        assert "mod_to_remove" not in favorites_after

    @pytest.mark.asyncio
    async def test_remove_nonexistent_favorite(self, test_db):
        """Removing a non-existent favorite returns False."""
        from app.services.catalog_favorite import CatalogFavoriteService

        result = await CatalogFavoriteService.remove(test_db, "nonexistent_module")
        assert result is False

    @pytest.mark.asyncio
    async def test_favorite_persistence_across_sessions(self):
        """Favorites persist across DB sessions (prove it's a real table)."""
        from app.models.catalog_favorite import CatalogFavorite
        from app.services.catalog_favorite import CatalogFavoriteService

        # Create a persistent in-memory engine (shared across sessions)
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Session 1: Add favorites
        AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with AsyncSessionLocal() as session1:
            await CatalogFavoriteService.add(session1, "persistent_mod_1")
            await CatalogFavoriteService.add(session1, "persistent_mod_2")
            favorites1 = await CatalogFavoriteService.list_ids(session1)
            assert favorites1 == {"persistent_mod_1", "persistent_mod_2"}

        # Session 2: Read favorites (should still be there)
        async with AsyncSessionLocal() as session2:
            favorites2 = await CatalogFavoriteService.list_ids(session2)
            assert favorites2 == {"persistent_mod_1", "persistent_mod_2"}

        # Session 3: Remove one and verify
        async with AsyncSessionLocal() as session3:
            removed = await CatalogFavoriteService.remove(session3, "persistent_mod_1")
            assert removed is True
            favorites3 = await CatalogFavoriteService.list_ids(session3)
            assert favorites3 == {"persistent_mod_2"}

        # Session 4: Verify removal persisted
        async with AsyncSessionLocal() as session4:
            favorites4 = await CatalogFavoriteService.list_ids(session4)
            assert favorites4 == {"persistent_mod_2"}

        await engine.dispose()
