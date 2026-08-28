"""
Fase 11 Slice 8 — Notificação de fonte indisponível (source unavailable notification)

Tests for detecting when a catalog source transitions from available→unavailable
and creating a notification only on that transition (no duplicate notifications).
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func, text

from app.package_manager.catalog_aggregator import CatalogAggregator
from app.package_manager.catalog_source import CatalogSource
from app.package_manager.models import PackageInfo
from app.models.notifications import Notification
from app.db.database import Base


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


class TestSourceAvailableTransition:
    """Test detection of source availability transitions and notification creation."""

    @pytest.mark.asyncio
    async def test_source_unavailable_creates_notification_on_transition(self, test_db):
        """
        When a source transitions from available→unavailable, exactly 1 notification
        should be created with source_id in the message.

        Scenario:
        1. First fetch: provider returns 1 package (success)
        2. Second fetch: provider returns [] (simulating network failure)
        3. Verify: 1 notification created with title mentioning the source is unavailable
        """
        aggregator = CatalogAggregator()

        pkg = PackageInfo(
            module_id="test_module",
            name="Test Module",
            version="1.0.0",
            category="Test",
            vendor="TestVendor",
            author="TestAuthor",
            description="Test",
            source=CatalogSource.CUSTOM_CATALOG,
            source_url="https://example.com",
        )

        mock_provider = AsyncMock()
        test_source_id = "test_custom_source"

        # First call: success (1 package returned)
        mock_provider.list_available = AsyncMock(return_value=[pkg])
        result1 = await aggregator._fetch_source(
            test_source_id, mock_provider, "1.0.0", force_refresh=False, db=test_db
        )
        assert result1 == [pkg]

        # Clear notifications from before
        await test_db.execute(text("DELETE FROM notifications"))
        await test_db.commit()

        # Second call: failure (empty list, simulating network error)
        mock_provider.list_available = AsyncMock(return_value=[])
        result2 = await aggregator._fetch_source(
            test_source_id, mock_provider, "1.0.0", force_refresh=True, db=test_db
        )
        assert result2 == [], "Should return empty when provider fails"

        # Verify: exactly 1 notification was created about source unavailability
        stmt = select(func.count(Notification.id)).where(
            Notification.title.like("%indisponível%")
        )
        count = await test_db.execute(stmt)
        notification_count = count.scalar()
        assert notification_count == 1, f"Expected 1 notification, got {notification_count}"

    @pytest.mark.asyncio
    async def test_no_duplicate_notification_on_repeated_failure(self, test_db):
        """
        If a source fails multiple times in a row, only ONE notification should exist.
        Second failure should detect duplicate and skip creating a new notification.
        """
        aggregator = CatalogAggregator()

        pkg = PackageInfo(
            module_id="test_module",
            name="Test Module",
            version="1.0.0",
            category="Test",
            vendor="TestVendor",
            author="TestAuthor",
            description="Test",
            source=CatalogSource.CUSTOM_CATALOG,
            source_url="https://example.com",
        )

        mock_provider = AsyncMock()
        test_source_id = "test_custom_source_2"

        # First call: success — establishes that source was available
        mock_provider.list_available = AsyncMock(return_value=[pkg])
        result1 = await aggregator._fetch_source(
            test_source_id, mock_provider, "1.0.0", force_refresh=False, db=test_db
        )
        assert result1 == [pkg], "First call should return package"
        assert aggregator._source_availability.get(test_source_id) is True

        # Second call: failure (returns empty list)
        mock_provider.list_available = AsyncMock(return_value=[])
        result2 = await aggregator._fetch_source(
            test_source_id, mock_provider, "1.0.0", force_refresh=True, db=test_db
        )
        assert result2 == [], "Second call should return empty (source now unavailable)"

        # Count notifications after first failure
        stmt = select(func.count(Notification.id)).where(
            Notification.title == "Catálogo indisponível"
        )
        count1 = (await test_db.execute(stmt)).scalar()
        assert count1 == 1, f"Expected 1 notification after first failure, got {count1}"

        # Third call: still failing
        result3 = await aggregator._fetch_source(
            test_source_id, mock_provider, "1.0.0", force_refresh=True, db=test_db
        )
        assert result3 == [], "Third call should return empty"

        # Verify: still only 1 notification (not 2) — dedupe worked
        count2 = (await test_db.execute(stmt)).scalar()
        assert count2 == 1, f"Expected 1 notification after repeated failures (dedupe), got {count2}"
