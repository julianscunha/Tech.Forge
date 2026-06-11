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
