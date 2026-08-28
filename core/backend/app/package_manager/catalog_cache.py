"""
Catalog Cache — Fase 11 Slice 4 §18

In-memory cache with TTL per catalog source. One entry per source_id,
stores list[PackageInfo] + fetched_at timestamp.

Não precisa de thread-safety complexa — projeto é single-process asyncio.
"""

from datetime import datetime, timedelta
from typing import Optional

from app.package_manager.models import PackageInfo


class CatalogCache:
    """In-memory cache for catalog packages with TTL support."""

    def __init__(self, ttl_seconds: int = 900):  # 15 minutes default
        """Initialize cache with TTL (in seconds)."""
        self.ttl_seconds = ttl_seconds
        # Format: {source_id: {"packages": list[PackageInfo], "fetched_at": datetime}}
        self._cache: dict[str, dict] = {}

    def get(self, source_id: str) -> Optional[list[PackageInfo]]:
        """
        Get cached packages for a source if still within TTL.
        Returns None if cache miss or TTL expired.
        """
        if source_id not in self._cache:
            return None

        entry = self._cache[source_id]
        fetched_at = entry["fetched_at"]
        now = datetime.now()

        # Check if TTL has expired
        if now - fetched_at > timedelta(seconds=self.ttl_seconds):
            # TTL expired, remove and return None
            del self._cache[source_id]
            return None

        return entry["packages"]

    def set(self, source_id: str, packages: list[PackageInfo]) -> None:
        """Store packages for a source with current timestamp."""
        self._cache[source_id] = {
            "packages": packages,
            "fetched_at": datetime.now(),
        }

    def invalidate(self, source_id: str) -> None:
        """Remove a source's cache entry immediately (ignore TTL)."""
        if source_id in self._cache:
            del self._cache[source_id]


# Singleton instance
catalog_cache = CatalogCache()
