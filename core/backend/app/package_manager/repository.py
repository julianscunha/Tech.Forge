"""
Repository Provider
====================
Abstraction layer between the Package Manager and the physical storage of
.mod packages.

The Marketplace must never depend directly on the file system — it always
goes through a RepositoryProvider. This allows Phase 5 to add a
RemoteRepositoryProvider without changing the Package Manager.

Current implementations:
  LocalRepositoryProvider  — scans modules/repository/ for .mod files
  RemoteRepositoryProvider — stub; will call a REST API in Phase 5
"""
from __future__ import annotations

import hashlib
import json
import logging
import zipfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

import yaml

from app.core.settings import settings
from app.package_manager.catalog_source import CatalogSource
from app.package_manager.models import PackageInfo

logger = logging.getLogger("techforge.repository")


# ── Abstract base ─────────────────────────────────────────────────────────────

class RepositoryProvider(ABC):
    """
    Abstract interface for a module repository.

    The Package Manager interacts exclusively with this interface;
    it never reads the file system or calls HTTP APIs directly.
    """

    @abstractmethod
    async def list_available(self, platform_version: str) -> list[PackageInfo]:
        """Return all packages available in this repository."""

    @abstractmethod
    async def get_package(self, module_id: str, platform_version: str) -> Optional[PackageInfo]:
        """Return metadata for a single package, or None if not found."""

    @abstractmethod
    async def fetch_mod_path(self, module_id: str) -> Optional[Path]:
        """
        Return the local filesystem path to the .mod file for installation.
        For remote providers, this downloads the file to cache/ first.
        """


# ── Local implementation ──────────────────────────────────────────────────────

class LocalRepositoryProvider(RepositoryProvider):
    """
    Reads .mod files from modules/repository/.

    Provides full offline functionality for Phase 4.
    Phase 5 extension: RemoteRepositoryProvider will download packages
    from a REST API and cache them here before returning the path.
    """

    def __init__(
        self,
        repository_path: Optional[Path] = None,
        cache_path: Optional[Path] = None,
    ) -> None:
        self._repo  = repository_path or settings.MODULES_REPOSITORY_PATH
        self._cache = cache_path or (settings.MODULES_REPOSITORY_PATH.parent / "cache")
        self._repo.mkdir(parents=True, exist_ok=True)
        self._cache.mkdir(parents=True, exist_ok=True)

    async def list_available(self, platform_version: str) -> list[PackageInfo]:
        """Scan repository/ for .mod files and return their PackageInfo."""
        packages: list[PackageInfo] = []
        for mod_file in sorted(self._repo.glob("*.mod")):
            info = await self._read_mod(mod_file, platform_version)
            if info:
                packages.append(info)
        return packages

    async def get_package(self, module_id: str, platform_version: str) -> Optional[PackageInfo]:
        # Find the most recent .mod file for this module_id
        candidates = sorted(
            self._repo.glob(f"{module_id}-*.mod"),
            key=lambda p: p.name,
            reverse=True,
        )
        if not candidates:
            return None
        return await self._read_mod(candidates[0], platform_version)

    async def fetch_mod_path(self, module_id: str) -> Optional[Path]:
        """Return path to the latest .mod file for module_id."""
        candidates = sorted(
            self._repo.glob(f"{module_id}-*.mod"),
            key=lambda p: p.name,
            reverse=True,
        )
        return candidates[0] if candidates else None

    async def store_upload(self, filename: str, content: bytes) -> Path:
        """
        Accept a manually uploaded .mod file and store it in cache/.
        Returns the path to the stored file for immediate installation.
        """
        dest = self._cache / filename
        dest.write_bytes(content)
        logger.info("Manual upload stored: %s (%d bytes)", dest, len(content))
        return dest

    # ── Internal ──────────────────────────────────────────────────────────────

    async def _read_mod(self, mod_path: Path, platform_version: str) -> Optional[PackageInfo]:
        """Extract manifest.yaml from a .mod file and return PackageInfo."""
        try:
            with zipfile.ZipFile(mod_path) as zf:
                if "manifest.yaml" not in zf.namelist():
                    logger.warning("No manifest.yaml in %s", mod_path.name)
                    return None
                raw: dict = yaml.safe_load(zf.read("manifest.yaml").decode("utf-8")) or {}

            info = PackageInfo.from_manifest_dict(raw, mod_path, platform_version)

            # Compute checksum of the .mod file for future signature verification
            if not info.checksum:
                info.checksum = hashlib.sha256(mod_path.read_bytes()).hexdigest()

            return info
        except (zipfile.BadZipFile, yaml.YAMLError, KeyError) as exc:
            logger.warning("Could not read %s: %s", mod_path.name, exc)
            return None


# ── Official Catalog Provider (index.json) ────────────────────────────────────

class OfficialCatalogProvider(RepositoryProvider):
    """
    Fetches module catalog from a remote index.json file.

    Used by the official Tech.Forge Modules catalog and any compatible
    index-based catalogs. Downloads only metadata (index.json), not the
    full .mod files — those are downloaded on demand during installation.
    """

    def __init__(
        self,
        base_url: str,
        cache_path: Optional[Path] = None,
    ) -> None:
        """
        Initialize the official catalog provider.

        Args:
            base_url: Base URL where index.json is located
                      (e.g., https://raw.githubusercontent.com/owner/repo/main)
            cache_path: Where to store downloaded .mod files (default: modules/cache/)
        """
        self._base_url = base_url.rstrip("/")
        self._cache = cache_path or (settings.MODULES_REPOSITORY_PATH.parent / "cache")
        self._cache.mkdir(parents=True, exist_ok=True)

    async def list_available(self, platform_version: str) -> list[PackageInfo]:
        """Fetch and parse index.json from the remote catalog."""
        import httpx

        index_url = f"{self._base_url}/index.json"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(index_url, timeout=10.0)

                # Check for HTTP errors
                if response.status_code >= 400:
                    logger.warning(
                        "Failed to fetch catalog from %s: HTTP %d",
                        index_url,
                        response.status_code,
                    )
                    return []

            index_data = response.json()
            packages: list[PackageInfo] = []

            for module_entry in index_data.get("modules", []):
                info = PackageInfo.from_manifest_dict(
                    module_entry,
                    source_path=None,
                    platform_version=platform_version,
                )
                info.source = CatalogSource.OFFICIAL_CATALOG
                info.source_url = module_entry.get("mod_url")
                packages.append(info)

            return packages

        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            logger.warning(
                "Failed to fetch catalog from %s: %s",
                index_url,
                exc,
            )
            return []
        except Exception as exc:
            logger.warning(
                "Unexpected error fetching catalog from %s: %s",
                index_url,
                exc,
            )
            return []

    async def get_package(self, module_id: str, platform_version: str) -> Optional[PackageInfo]:
        """Get a single package from the catalog by ID."""
        packages = await self.list_available(platform_version)
        for pkg in packages:
            if pkg.module_id == module_id:
                return pkg
        return None

    async def fetch_mod_path(self, module_id: str) -> Optional[Path]:
        """Download the .mod file for a module and return its local path."""
        import httpx

        # Get the package metadata (which includes the mod_url)
        pkg = await self.get_package(module_id, "1.0.0")
        if not pkg or not pkg.source_url:
            logger.warning("Package %s not found in catalog or has no mod_url", module_id)
            return None

        mod_url = pkg.source_url
        # If the URL is relative (just a filename), prepend the base URL
        if not mod_url.startswith("http"):
            mod_url = f"{self._base_url}/{mod_url}"

        # Extract filename from URL for local cache
        cache_filename = mod_url.split("/")[-1]
        cache_path = self._cache / cache_filename

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(mod_url, timeout=30.0)
                response.raise_for_status()

            cache_path.write_bytes(response.content)
            logger.info(
                "Downloaded module %s to cache: %s (%d bytes)",
                module_id,
                cache_path,
                len(response.content),
            )
            return cache_path

        except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError) as exc:
            logger.warning(
                "Failed to download module %s from %s: %s",
                module_id,
                mod_url,
                exc,
            )
            return None
        except Exception as exc:
            logger.warning(
                "Unexpected error downloading module %s: %s",
                module_id,
                exc,
            )
            return None


# ── Remote stub ───────────────────────────────────────────────────────────────

class RemoteRepositoryProvider(RepositoryProvider):
    """
    Phase 5 stub — will call the TechForge Marketplace REST API.

    Stores downloaded .mod files in modules/cache/ so subsequent
    installs don't require a network round-trip.
    """

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url
        self._cache = settings.MODULES_REPOSITORY_PATH.parent / "cache"
        self._cache.mkdir(parents=True, exist_ok=True)

    async def list_available(self, platform_version: str) -> list[PackageInfo]:
        raise NotImplementedError(
            "RemoteRepositoryProvider will be implemented in Phase 5."
        )

    async def get_package(self, module_id: str, platform_version: str) -> Optional[PackageInfo]:
        raise NotImplementedError(
            "RemoteRepositoryProvider will be implemented in Phase 5."
        )

    async def fetch_mod_path(self, module_id: str) -> Optional[Path]:
        raise NotImplementedError(
            "RemoteRepositoryProvider will be implemented in Phase 5."
        )
