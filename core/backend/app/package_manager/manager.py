"""
Package Manager
================
Central service for all module lifecycle operations.

Responsibilities:
  - install a module from a .mod file
  - update an installed module from a newer .mod file
  - remove an installed module
  - hot-reload the registry after any operation
  - record every operation in the OperationLog
  - validate compatibility before any install/update

The Package Manager is the ONLY component that writes to modules/installed/.
All other components (Marketplace API, CLI) call this service.

Hot reload strategy (Phase 4):
  After install / update / remove, the Package Manager calls
  ModuleLoader.scan_installed() to rebuild the in-memory registry
  without restarting the process.
"""
from __future__ import annotations

import hashlib
import asyncio
import json
import logging
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml

from app.core.settings import settings
from app.module_engine.loader import ModuleLoader
from app.module_engine.registry import registry
from app.module_engine import journal as loader_journal
from app.module_engine.enums import ModuleStatus
from app.package_manager.enums import (
    InstallStatus, RemoveStatus, UpdateStatus, CompatibilityLevel,
)
from app.package_manager.compatibility import check_compatibility
from app.package_manager.models import PackageInfo
from app.package_manager.operation_log import operation_log
from app.package_manager.repository import LocalRepositoryProvider, RepositoryProvider

logger = logging.getLogger("techforge.package_manager")


# ── Operation results ─────────────────────────────────────────────────────────

class InstallResult:
    def __init__(self, status: InstallStatus, module_id: str, version: str, message: str):
        self.status    = status
        self.module_id = module_id
        self.version   = version
        self.message   = message
        self.success   = status == InstallStatus.SUCCESS


class RemoveResult:
    def __init__(self, status: RemoveStatus, module_id: str, message: str):
        self.status    = status
        self.module_id = module_id
        self.message   = message
        self.success   = status == RemoveStatus.SUCCESS


class UpdateResult:
    def __init__(self, status: UpdateStatus, module_id: str,
                 from_version: str, to_version: str, message: str):
        self.status       = status
        self.module_id    = module_id
        self.from_version = from_version
        self.to_version   = to_version
        self.message      = message
        self.success      = status == UpdateStatus.SUCCESS


# ── Package Manager ───────────────────────────────────────────────────────────

class PackageManager:
    """
    Singleton service for module lifecycle management.

    Import the process-level instance:
        from app.package_manager.manager import package_manager
    """

    def __init__(
        self,
        installed_path: Optional[Path]       = None,
        cache_path:     Optional[Path]       = None,
        repository:     Optional[RepositoryProvider] = None,
        use_global_registry: bool = True,   # Fase 4: fonte única de verdade
    ) -> None:
        self._installed = installed_path or settings.MODULES_INSTALLED_PATH
        self._cache     = cache_path or (self._installed.parent / "cache")
        self._installed.mkdir(parents=True, exist_ok=True)
        self._cache.mkdir(parents=True, exist_ok=True)
        self._repo = repository or LocalRepositoryProvider()
        # Fonte única de verdade (decisão 2026-08-25): listagens leem o registry
        # global; PMs isolados (testes com tmp_path) usam registry próprio.
        self._use_global_registry = use_global_registry

    @property
    def _read_registry(self):
        """Registry para leitura das listagens — global (singleton) ou local persistente."""
        if self._use_global_registry:
            from app.module_engine.registry import registry
            return registry
        if not hasattr(self, "_isolated_registry"):
            from app.module_engine.registry import ModuleRegistry
            from app.module_engine.loader import ModuleLoader
            self._isolated_registry = ModuleRegistry()
            loader = ModuleLoader(installed_path=self._installed,
                                  target_registry=self._isolated_registry)
            # pode rodar dentro de event loop existente (rotas async) ou fora (testes)
            try:
                asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(1) as pool:
                    pool.submit(asyncio.run, loader.scan_installed()).result()
            except RuntimeError:
                asyncio.run(loader.scan_installed())
        return self._isolated_registry

    # ── Install ───────────────────────────────────────────────────────────────

    async def install(self, mod_path: Path) -> InstallResult:
        """
        Install a module from a .mod file path.

        Steps:
          1. Validate the .mod archive integrity
          2. Extract and parse manifest
          3. Check platform compatibility
          4. Check for duplicate installation
          5. Extract to modules/installed/<module_id>/
          6. Hot-reload registry
        """
        mod_path = Path(mod_path)

        # ── 1. Archive integrity ──────────────────────────────────────────────
        if not mod_path.exists():
            return self._fail_install("unknown", "0.0.0",
                                      f".mod file not found: {mod_path}")

        if not zipfile.is_zipfile(mod_path):
            return self._fail_install("unknown", "0.0.0",
                                      f"File is not a valid .mod archive: {mod_path.name}")

        # ── 2. Read manifest ──────────────────────────────────────────────────
        try:
            with zipfile.ZipFile(mod_path) as zf:
                if "manifest.yaml" not in zf.namelist():
                    return self._fail_install("unknown", "0.0.0",
                                              "Archive missing manifest.yaml")
                raw: dict = yaml.safe_load(
                    zf.read("manifest.yaml").decode("utf-8")
                ) or {}
        except (zipfile.BadZipFile, yaml.YAMLError) as exc:
            return self._fail_install("unknown", "0.0.0", str(exc))

        module_id = str(raw.get("id", "")).strip()
        version   = str(raw.get("version", "0.0.0")).strip()

        if not module_id:
            return self._fail_install("unknown", version, "Manifest missing required field: id")

        # ── 3. Compatibility ──────────────────────────────────────────────────
        compat = check_compatibility(
            settings.PLATFORM_VERSION,
            str(raw.get("platform_min_version", "0.0.0")),
            str(raw.get("platform_max_version", "999.999.999")),
        )
        if compat == CompatibilityLevel.INCOMPATIBLE:
            msg = (f"Module {module_id} v{version} is incompatible with "
                   f"platform v{settings.PLATFORM_VERSION}.")
            operation_log.record("install", module_id, version, "incompatible", msg)
            return InstallResult(InstallStatus.INCOMPATIBLE, module_id, version, msg)

        # ── 3.5 Guard: mesmo ID em estado inválido/incompatível no registry ──
        existing_entry = registry.get(module_id)
        if existing_entry and existing_entry.status in (
            ModuleStatus.INVALID, ModuleStatus.INCOMPATIBLE,
        ):
            msg = (f"Module '{module_id}' cannot be installed: it is registered as "
                   f"{existing_entry.status.value}. Remove it first to retry.")
            operation_log.record("install", module_id, version,
                                 f"blocked_{existing_entry.status.value.lower()}", msg)
            logger.warning(msg)
            return InstallResult(InstallStatus.FAILED, module_id, version, msg)

        # ── 4. Duplicate check ────────────────────────────────────────────────
        target_dir = self._installed / module_id
        if target_dir.exists():
            msg = f"Module '{module_id}' is already installed. Use update to upgrade."
            operation_log.record("install", module_id, version, "already_installed", msg)
            return InstallResult(InstallStatus.ALREADY_INSTALLED, module_id, version, msg)

        # ── 5. Extract ────────────────────────────────────────────────────────
        try:
            extract_tmp = self._cache / f"_extract_{module_id}"
            if extract_tmp.exists():
                shutil.rmtree(extract_tmp)
            extract_tmp.mkdir(parents=True)

            with zipfile.ZipFile(mod_path) as zf:
                # Only extract module content — skip META-INF/
                for member in zf.namelist():
                    if not member.startswith("META-INF/"):
                        zf.extract(member, extract_tmp)

            # Atomic move: tmp → installed/<module_id>
            shutil.move(str(extract_tmp), str(target_dir))
        except Exception as exc:
            if extract_tmp.exists():
                shutil.rmtree(extract_tmp, ignore_errors=True)
            return self._fail_install(module_id, version, f"Extraction failed: {exc}")

        # ── 6. Hot-reload registry ────────────────────────────────────────────
        await self._hot_reload()

        msg = f"Module '{module_id}' v{version} installed successfully."
        operation_log.record("install", module_id, version, "success", msg,
                              source=str(mod_path.name))
        logger.info(msg)
        return InstallResult(InstallStatus.SUCCESS, module_id, version, msg)

    # ── Remove ────────────────────────────────────────────────────────────────

    async def remove(self, module_id: str) -> RemoveResult:
        """
        Remove an installed module.

        Steps:
          1. Verify it exists in the registry
          2. Deregister from in-memory registry
          3. Delete the installed directory
          4. Hot-reload registry
        """
        target_dir = self._installed / module_id

        if not target_dir.exists():
            msg = f"Module '{module_id}' is not installed."
            operation_log.record("remove", module_id, "unknown", "not_found", msg)
            return RemoveResult(RemoveStatus.NOT_FOUND, module_id, msg)

        # Read version before removing
        version = "unknown"
        try:
            mf = target_dir / "manifest.yaml"
            if mf.exists():
                raw = yaml.safe_load(mf.read_text(encoding="utf-8")) or {}
                version = str(raw.get("version", "unknown"))
        except Exception:
            pass

        # Deregister first so the registry is consistent during file deletion
        registry.deregister(module_id)

        try:
            shutil.rmtree(target_dir)
        except Exception as exc:
            # Re-register on failure to keep registry in sync
            await self._hot_reload()
            return self._fail_remove(module_id, f"Failed to delete files: {exc}")

        await self._hot_reload()

        msg = f"Module '{module_id}' v{version} removed successfully."
        operation_log.record("remove", module_id, version, "success", msg)
        logger.info(msg)
        return RemoveResult(RemoveStatus.SUCCESS, module_id, msg)

    # ── Update ────────────────────────────────────────────────────────────────

    async def update(self, module_id: str, mod_path: Path) -> UpdateResult:
        """
        Update an installed module from a newer .mod file.

        Steps:
          1. Verify current installation
          2. Parse new manifest
          3. Check version is actually newer
          4. Compatibility check
          5. Backup current version to cache/
          6. Extract new version
          7. Hot-reload registry
        """
        mod_path = Path(mod_path)
        target_dir = self._installed / module_id

        if not target_dir.exists():
            msg = f"Module '{module_id}' is not installed. Use install instead."
            operation_log.record("update", module_id, "unknown", "not_found", msg)
            return UpdateResult(UpdateStatus.NOT_FOUND, module_id, "?", "?", msg)

        # Read current version
        from_version = "unknown"
        try:
            old_mf = target_dir / "manifest.yaml"
            if old_mf.exists():
                old_raw = yaml.safe_load(old_mf.read_text(encoding="utf-8")) or {}
                from_version = str(old_raw.get("version", "unknown"))
        except Exception:
            pass

        # Read new manifest
        if not zipfile.is_zipfile(mod_path):
            return self._fail_update(module_id, from_version, "?",
                                     f"Not a valid .mod archive: {mod_path.name}")
        try:
            with zipfile.ZipFile(mod_path) as zf:
                raw: dict = yaml.safe_load(
                    zf.read("manifest.yaml").decode("utf-8")
                ) or {}
        except Exception as exc:
            return self._fail_update(module_id, from_version, "?", str(exc))

        to_version = str(raw.get("version", "0.0.0")).strip()

        # Version must be newer (or forced)
        if _vt(to_version) <= _vt(from_version):
            msg = f"New version ({to_version}) is not newer than installed ({from_version})."
            operation_log.record("update", module_id, to_version, "up_to_date", msg)
            return UpdateResult(UpdateStatus.UP_TO_DATE, module_id, from_version, to_version, msg)

        # Compatibility check
        compat = check_compatibility(
            settings.PLATFORM_VERSION,
            str(raw.get("platform_min_version", "0.0.0")),
            str(raw.get("platform_max_version", "999.999.999")),
        )
        if compat == CompatibilityLevel.INCOMPATIBLE:
            msg = (f"New version {to_version} is incompatible with "
                   f"platform v{settings.PLATFORM_VERSION}. Update blocked.")
            operation_log.record("update", module_id, to_version, "incompatible", msg)
            return UpdateResult(UpdateStatus.INCOMPATIBLE, module_id, from_version, to_version, msg)

        # Backup current version
        backup = self._cache / f"{module_id}-{from_version}.bak"
        try:
            if backup.exists():
                shutil.rmtree(backup)
            shutil.copytree(str(target_dir), str(backup))
        except Exception as exc:
            logger.warning("Backup failed for %s: %s", module_id, exc)

        # Extract new version
        try:
            extract_tmp = self._cache / f"_update_{module_id}"
            if extract_tmp.exists():
                shutil.rmtree(extract_tmp)
            extract_tmp.mkdir(parents=True)

            with zipfile.ZipFile(mod_path) as zf:
                for member in zf.namelist():
                    if not member.startswith("META-INF/"):
                        zf.extract(member, extract_tmp)

            shutil.rmtree(target_dir)
            shutil.move(str(extract_tmp), str(target_dir))
        except Exception as exc:
            # Attempt rollback from backup
            if backup.exists():
                try:
                    if target_dir.exists():
                        shutil.rmtree(target_dir)
                    shutil.copytree(str(backup), str(target_dir))
                    logger.info("Rollback to %s v%s succeeded.", module_id, from_version)
                except Exception:
                    pass
            return self._fail_update(module_id, from_version, to_version,
                                     f"Extraction failed: {exc}")

        await self._hot_reload()

        msg = (f"Module '{module_id}' updated from v{from_version} to v{to_version}.")
        operation_log.record("update", module_id, to_version, "success", msg,
                             from_version=from_version)
        logger.info(msg)
        return UpdateResult(UpdateStatus.SUCCESS, module_id, from_version, to_version, msg)

    # ── Query helpers ─────────────────────────────────────────────────────────

    async def list_available(self) -> list[PackageInfo]:
        """List all packages available in repository/."""
        packages = await self._repo.list_available(settings.PLATFORM_VERSION)
        # Annotate with installed state from the read registry (fonte única)
        for pkg in packages:
            entry = self._read_registry.get(pkg.module_id)
            if entry:
                pkg.is_installed      = True
                pkg.installed_version = entry.version
                pkg.install_date      = entry.install_date
                pkg.is_enabled        = (entry.status != ModuleStatus.DISABLED)
        return packages

    async def list_installed(self) -> list[PackageInfo]:
        """Return PackageInfo for every module in the read registry (fonte única)."""
        result = []
        for entry in self._read_registry.all():
            if entry.status == ModuleStatus.INVALID:
                continue  # invalid modules have no package to show
            pkg = PackageInfo(
                module_id   = entry.module_id,
                name        = entry.name,
                version     = entry.version,
                category    = entry.category,
                vendor      = entry.vendor,
                author      = entry.author,
                description = entry.description,
                platform_min_version=entry.platform_min_version,
                platform_max_version=entry.platform_max_version,
                compatibility=check_compatibility(
                    settings.PLATFORM_VERSION,
                    entry.platform_min_version,
                    entry.platform_max_version,
                ),
                icon=entry.icon,
                color=entry.color,
                order=entry.order,
                is_installed=True,
                is_enabled=(entry.status.value != "DISABLED"),
                installed_version=entry.version,
                install_date=entry.install_date,
            )
            result.append(pkg)
        return result

    async def list_updates(self) -> list[PackageInfo]:
        """Return packages that have a newer version available in repository/."""
        available  = await self.list_available()
        return [p for p in available if p.has_update]

    # ── Hot reload ────────────────────────────────────────────────────────────

    async def _hot_reload(self) -> None:
        """
        Rebuild the in-memory registry from modules/installed/ without
        restarting the FastAPI process. Also syncs the DB module table
        (dashboard counters).
        """
        loader = ModuleLoader(installed_path=self._installed)
        result = await loader.scan_installed()
        loader_journal.store(result)

        if self._use_global_registry:
            from app.services.registry_sync import sync_from_request
            await sync_from_request()

        logger.info(
            "Hot reload: %d installed, %d invalid.",
            result.installed, result.invalid,
        )

    # ── Error helpers ─────────────────────────────────────────────────────────

    def _fail_install(self, module_id: str, version: str, msg: str) -> InstallResult:
        operation_log.record("install", module_id, version, "failed", msg)
        logger.error("Install failed [%s]: %s", module_id, msg)
        return InstallResult(InstallStatus.FAILED, module_id, version, msg)

    def _fail_remove(self, module_id: str, msg: str) -> RemoveResult:
        operation_log.record("remove", module_id, "unknown", "failed", msg)
        logger.error("Remove failed [%s]: %s", module_id, msg)
        return RemoveResult(RemoveStatus.FAILED, module_id, msg)

    def _fail_update(self, module_id: str, from_v: str, to_v: str, msg: str) -> UpdateResult:
        operation_log.record("update", module_id, to_v, "failed", msg, from_version=from_v)
        logger.error("Update failed [%s]: %s", module_id, msg)
        return UpdateResult(UpdateStatus.FAILED, module_id, from_v, to_v, msg)


# ── Module-level singleton ────────────────────────────────────────────────────
package_manager = PackageManager()


def _vt(v: str) -> tuple[int, ...]:
    try:
        return tuple(int(p) for p in str(v).split("."))
    except (ValueError, TypeError):
        return (0, 0, 0)
