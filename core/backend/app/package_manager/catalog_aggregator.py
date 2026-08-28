"""
Catalog Aggregator — Fase 11 Slice 4 §18/§19/§20

Coordena múltiplas fontes (LOCAL, OFFICIAL, CUSTOM) em paralelo com cache TTL
e detecção de conflitos. Uma fonte indisponível não impede as outras.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.package_manager.catalog_cache import CatalogCache, catalog_cache
from app.package_manager.catalog_source import CatalogSource
from app.package_manager.conflicts import detect_conflicts
from app.package_manager.models import PackageInfo
from app.package_manager.repository import (
    LocalRepositoryProvider,
    OfficialCatalogProvider,
    CustomCatalogProvider,
)
from app.services.catalog_source import CatalogSourceService

logger = logging.getLogger("techforge.catalog_aggregator")


class CatalogAggregator:
    """Aggregates packages from multiple sources with caching and parallelization."""

    def __init__(
        self,
        cache: Optional[CatalogCache] = None,
        cache_ttl_seconds: int = 900,
    ):
        """
        Initialize aggregator.

        Args:
            cache: CatalogCache instance (uses singleton if not provided)
            cache_ttl_seconds: TTL for cache entries (only used if cache is None)
        """
        self.cache = cache or catalog_cache
        self.local_provider = LocalRepositoryProvider(repository_path=settings.MODULES_REPOSITORY_PATH)
        self.official_provider = OfficialCatalogProvider(
            base_url="https://techforge.io/catalog"  # placeholder
        )
        # Track source availability for detecting transitions
        # {source_id: bool} where True = last fetch was successful (non-empty)
        self._source_availability: dict[str, bool] = {}

    async def _get_custom_providers(
        self, db: AsyncSession
    ) -> list[CustomCatalogProvider]:
        """Get CustomCatalogProviders for all enabled custom sources."""
        sources = await CatalogSourceService.list_all(db)
        providers = []

        for source in sources:
            if (
                source.type == CatalogSource.CUSTOM_CATALOG.value
                and source.enabled
            ):
                provider = CustomCatalogProvider(repo_url=source.url)
                providers.append((source.id, provider))

        return providers

    async def list_all_available(
        self,
        db: AsyncSession,
        platform_version: str,
        force_refresh: bool = False,
    ) -> tuple[list[PackageInfo], dict[str, list[PackageInfo]]]:
        """
        List all available packages from enabled sources.

        Order: LOCAL → OFFICIAL_CATALOG → CUSTOM_CATALOG (by creation date).
        Fetches run in parallel (asyncio.gather), but the result order is
        fixed by *input* position, not by which network call returns
        first — gather() preserves input order regardless of completion
        order, so priority stays deterministic (spec §19: "não escolher
        arbitrariamente") even though the I/O itself is concurrent.

        Args:
            db: Database session
            platform_version: Platform version for compatibility checks
            force_refresh: If True, bypass cache and fetch all sources

        Returns:
            Tuple of (packages, conflicts) where:
            - packages: List of PackageInfo from all sources
            - conflicts: Dict[module_id, list[PackageInfo]] for modules in >1 source
        """
        custom_provider_pairs = await self._get_custom_providers(db)

        ordered_sources = [
            ("local", self.local_provider),
            ("official", self.official_provider),
            *custom_provider_pairs,
        ]

        results = await asyncio.gather(
            *(
                self._fetch_source(source_id, provider, platform_version, force_refresh, db)
                for source_id, provider in ordered_sources
            )
        )

        packages: list[PackageInfo] = []
        for result in results:
            packages.extend(result)

        conflicts = detect_conflicts(packages)

        return packages, conflicts

    async def _fetch_source(
        self,
        source_id: str,
        provider,
        platform_version: str,
        force_refresh: bool,
        db: AsyncSession,
    ) -> list[PackageInfo]:
        """
        Fetch from a single source, use cache if available, handle errors gracefully.

        Detects source availability transitions and creates notifications when a
        previously-available source becomes unavailable (returns empty list due to error).
        """
        try:
            if not force_refresh:
                cached = self.cache.get(source_id)
                if cached is not None:
                    return cached

            result = await provider.list_available(platform_version)

            # Track successful fetch (non-empty result)
            was_available = self._source_availability.get(source_id, False)
            is_available = len(result) > 0

            self._source_availability[source_id] = is_available

            # Detect transition: was available, now is NOT
            if was_available and not is_available:
                await self._notify_source_unavailable(db, source_id)

            self.cache.set(source_id, result)
            return result

        except Exception as e:
            logger.warning(
                f"Failed to fetch from source '{source_id}': {type(e).__name__}: {e}"
            )

            # Detect transition: was available (if we're catching exception), now is NOT
            was_available = self._source_availability.get(source_id, False)
            if was_available:
                self._source_availability[source_id] = False
                try:
                    await self._notify_source_unavailable(db, source_id)
                except Exception as notify_error:
                    logger.error(f"Failed to notify source unavailability for {source_id}: {notify_error}")

            # Don't propagate exception; other sources should still work
            return []

    async def _notify_source_unavailable(
        self, db: AsyncSession, source_id: str
    ) -> None:
        """
        Create a notification when a source becomes unavailable (transition detection).

        Uses dedupe pattern: only notifies if no identical notification already exists
        (same title + message). Prevents duplicate notifications on repeated failures.
        """
        from sqlalchemy import func, select
        from app.models.notifications import Notification
        from app.services.notifications import NotificationService

        title = "Catálogo indisponível"
        message = f"A fonte de catálogo '{source_id}' não está respondendo."

        # Dedupe: check if identical notification already exists
        existing = await db.execute(
            select(func.count(Notification.id)).where(
                Notification.title == title, Notification.message == message
            )
        )
        if existing.scalar() == 0:
            await NotificationService.create(
                db, level="warning", title=title, message=message, module_id=None
            )
