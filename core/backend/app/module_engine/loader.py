"""
ModuleLoader
============
Orchestrates the complete module lifecycle pipeline at platform startup:

  scan installed/ → validate structure → validate manifest
  → check compatibility → register in ModuleRegistry

This is the entry point called by FastAPI's lifespan handler.
It emits structured log events at every step so Developer Mode can
display a detailed loading journal in the UI.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.core.settings import settings
from app.module_engine.enums import ModuleStatus
from app.module_engine.manifest import ParsedManifest
from app.module_engine.registry import ModuleEntry, ModuleRegistry, registry
from app.module_engine.validator import ModuleValidator

logger = logging.getLogger("techforge.module_loader")


# ── Load event (Developer Mode) ───────────────────────────────────────────────

@dataclass
class LoadEvent:
    """One timestamped entry in the loader journal."""
    timestamp: datetime
    module_id: Optional[str]       # None for global messages
    level: str                     # "info" | "warning" | "error"
    message: str
    details: dict = field(default_factory=dict)


# ── Loader result ─────────────────────────────────────────────────────────────

@dataclass
class LoaderResult:
    """Summary returned after a full scan."""
    scanned:      int = 0
    installed:    int = 0
    disabled:     int = 0
    invalid:      int = 0
    incompatible: int = 0
    journal: list[LoadEvent] = field(default_factory=list)

    def add_event(
        self,
        message: str,
        level: str = "info",
        module_id: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> None:
        self.journal.append(LoadEvent(
            timestamp=datetime.utcnow(),
            module_id=module_id,
            level=level,
            message=message,
            details=details or {},
        ))


# ── Loader ────────────────────────────────────────────────────────────────────

class ModuleLoader:
    """
    Scans the installed modules directory, validates each module, and
    populates the ModuleRegistry.

    Phase 2: reads from modules/installed/ only (local mode).
    Phase 3 extension: scan_repository() will read modules/repository/ and
                       trigger download + install via Marketplace API.

    Usage (in FastAPI lifespan):
        loader = ModuleLoader()
        result = await loader.scan_installed()
    """

    def __init__(
        self,
        installed_path: Optional[Path] = None,
        target_registry: Optional[ModuleRegistry] = None,
    ) -> None:
        self._installed_path = installed_path or settings.MODULES_INSTALLED_PATH
        self._registry = target_registry or registry
        self._platform_version = settings.PLATFORM_VERSION

    # ── Public API ────────────────────────────────────────────────────────────

    async def scan_installed(self) -> LoaderResult:
        """
        Full startup scan.

        1. Clear the registry (idempotent — safe to call multiple times).
        2. Discover all candidate module directories.
        3. Validate and register each one.
        4. Return a LoaderResult with counts and the Developer Mode journal.
        """
        result = LoaderResult()

        result.add_event(
            f"Starting module scan in: {self._installed_path}",
            level="info",
        )

        self._registry.clear()

        if not self._installed_path.exists():
            result.add_event(
                f"Installed modules directory not found: {self._installed_path}",
                level="warning",
            )
            logger.warning("modules/installed/ directory missing; no modules loaded.")
            return result

        # Candidate directories: immediate children that are actual directories
        candidates = sorted(
            p for p in self._installed_path.iterdir()
            if p.is_dir() and not p.name.startswith(".")
        )

        result.scanned = len(candidates)
        result.add_event(f"Found {len(candidates)} candidate module(s).")

        for module_path in candidates:
            await self._load_one(module_path, result)

        result.add_event(
            f"Scan complete — installed: {result.installed}, "
            f"disabled: {result.disabled}, "
            f"invalid: {result.invalid}, "
            f"incompatible: {result.incompatible}",
            level="info",
        )

        logger.info(
            "Module scan complete: %d installed, %d invalid, %d incompatible",
            result.installed, result.invalid, result.incompatible,
        )

        return result

    # ── Internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _is_disabled(module_path: Path) -> bool:
        """Check the module's disable flag (data/state.json, written by deactivate)."""
        import json
        state_file = module_path / "data" / "state.json"
        if not state_file.is_file():
            return False
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
            return bool(state.get("disabled", False))
        except (OSError, ValueError):
            return False

    async def _load_one(self, module_path: Path, result: LoaderResult) -> None:
        """Validate and register a single module directory."""
        module_name = module_path.name
        result.add_event(
            f"Processing: {module_name}",
            module_id=module_name,
        )

        validation = ModuleValidator.validate(module_path, self._platform_version)

        # Log individual warnings
        for w in validation.warnings:
            logger.debug("Module %s warning: %s", module_name, w)
            result.add_event(w, level="warning", module_id=module_name)

        if not validation.is_valid:
            for err in validation.errors:
                logger.warning("Module %s error: %s", module_name, err)
                result.add_event(err, level="error", module_id=module_name)

            # Register the failed module so it's visible in the UI
            self._register_failed(
                module_id=module_name,
                status=validation.status,
                errors=validation.errors,
                warnings=validation.warnings,
                manifest=validation.manifest,
            )

            if validation.status == ModuleStatus.INCOMPATIBLE:
                result.incompatible += 1
            else:
                result.invalid += 1
            return

        # Happy path
        manifest = validation.manifest  # guaranteed non-None after is_valid=True

        # Fase 4 §10 — user directive: disabled modules save resources.
        # A module with a disable flag is registered as DISABLED: its entry_backend
        # is NOT mounted by the plugin loader and it stays out of the navigation.
        if self._is_disabled(module_path):
            entry = ModuleEntry.from_manifest(
                manifest=manifest,
                status=ModuleStatus.DISABLED,
                errors=[],
                warnings=validation.warnings,
            )
            self._registry.register(entry)
            result.disabled += 1
            result.add_event(
                f"Module '{manifest.id}' is disabled — skipping load.",
                level="info",
                module_id=manifest.id,
            )
            logger.info("Module disabled, not loaded: %s", manifest.id)
            return

        entry = ModuleEntry.from_manifest(
            manifest=manifest,
            status=ModuleStatus.INSTALLED,
            errors=[],
            warnings=validation.warnings,
        )
        self._registry.register(entry)
        result.installed += 1

        result.add_event(
            f"Registered '{manifest.name}' v{manifest.version} [{manifest.category}]",
            level="info",
            module_id=manifest.id,
            details={
                "vendor": manifest.vendor,
                "platform_min": manifest.platform_min_version,
                "platform_max": manifest.platform_max_version,
            },
        )
        logger.info(
            "Module loaded: %s v%s (%s)",
            manifest.name, manifest.version, manifest.category,
        )

    def _register_failed(
        self,
        module_id: str,
        status: ModuleStatus,
        errors: list[str],
        warnings: list[str],
        manifest: Optional[ParsedManifest],
    ) -> None:
        """Register a failed module so it appears in the UI with its error state."""
        if manifest is not None:
            entry = ModuleEntry.from_manifest(
                manifest=manifest,
                status=status,
                errors=errors,
                warnings=warnings,
            )
        else:
            # Manifest was unreadable — create a minimal placeholder entry
            entry = ModuleEntry(
                module_id=module_id,
                name=module_id,
                version="unknown",
                category="Unknown",
                vendor="Unknown",
                author="Unknown",
                description="Module failed to load.",
                status=status,
                install_date=datetime.utcnow(),
                errors=errors,
                warnings=warnings,
            )
        self._registry.register(entry)
