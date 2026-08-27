"""
ModuleRegistry
==============
Central in-memory registry of all modules discovered and loaded by the
Module Loader at startup.

This is a singleton-per-process store. The registry is the authoritative
source of truth for module state at runtime — the SQLite database is the
persistent complement for history and configuration.

Design notes:
- Thread-safe via asyncio: all writes happen during the startup scan,
  reads happen during request handling; no concurrent writes in Phase 2.
- Phase 3 (Marketplace): install() / uninstall() will mutate the registry
  at runtime and must add asyncio.Lock protection.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from app.module_engine.enums import ModuleStatus
from app.module_engine.manifest import ParsedManifest


# ── Runtime entry ─────────────────────────────────────────────────────────────

@dataclass
class ModuleEntry:
    """
    One entry in the module registry.  Combines manifest data with
    runtime state so callers don't need to juggle two objects.
    """
    # Identity
    module_id:   str
    name:        str
    version:     str
    category:    str
    vendor:      str
    author:      str
    description: str

    # Runtime state
    status:       ModuleStatus
    install_date: datetime
    errors:       list[str]  = field(default_factory=list)
    warnings:     list[str]  = field(default_factory=list)

    # Module type (Fase 8 §5) — "application" | "service"
    module_type: str = "application"

    # Compatibility window
    platform_min_version: str = "0.0.0"
    platform_max_version: str = "999.999.999"

    # Entry points (used by Plugin Loader in Phase 2 route injection)
    entry_backend:  Optional[str] = None
    entry_frontend: Optional[str] = None

    # UI display fields (from manifest)
    icon:  Optional[str] = None
    color: Optional[str] = None
    order: Optional[int] = None

    # Developer Mode — raw manifest payload
    manifest_raw: dict = field(default_factory=dict, repr=False)

    @property
    def is_active(self) -> bool:
        return self.status == ModuleStatus.INSTALLED

    @classmethod
    def from_manifest(
        cls,
        manifest: ParsedManifest,
        status: ModuleStatus,
        errors: list[str],
        warnings: list[str],
    ) -> "ModuleEntry":
        return cls(
            module_id=manifest.id,
            name=manifest.name,
            version=manifest.version,
            category=manifest.category,
            vendor=manifest.vendor,
            author=manifest.author,
            description=manifest.description,
            status=status,
            install_date=datetime.utcnow(),
            errors=errors,
            warnings=warnings,
            module_type=manifest.module_type,
            platform_min_version=manifest.platform_min_version,
            platform_max_version=manifest.platform_max_version,
            entry_backend=manifest.entry_backend,
            entry_frontend=manifest.entry_frontend,
            icon=manifest.icon,
            color=manifest.color,
            order=manifest.order,
            manifest_raw=manifest.raw,
        )


# ── Registry ──────────────────────────────────────────────────────────────────

class ModuleRegistry:
    """
    Central in-memory store for all discovered modules.

    Accessed by:
    - ModuleLoader         (writes during startup scan)
    - API route /modules   (reads for list and detail endpoints)
    - DashboardPage        (reads for status counters)
    - Developer Mode panel (reads manifest_raw)

    Phase 3 extension point:
    - install_from_marketplace() will call register() at runtime
    - uninstall() will call deregister() and reload the registry
    """

    def __init__(self) -> None:
        self._entries: dict[str, ModuleEntry] = {}

    # ── Writes ────────────────────────────────────────────────────────────────

    def register(self, entry: ModuleEntry) -> None:
        """Add or replace a module entry in the registry."""
        self._entries[entry.module_id] = entry

    def deregister(self, module_id: str) -> None:
        """Remove a module entry. No-op if not present."""
        self._entries.pop(module_id, None)

    def set_status(self, module_id: str, status: ModuleStatus) -> bool:
        """
        Update the status of an already-registered module.
        Returns True if the module was found; False otherwise.
        """
        entry = self._entries.get(module_id)
        if entry is None:
            return False
        entry.status = status
        return True

    def clear(self) -> None:
        """Remove all entries. Used during full re-scans."""
        self._entries.clear()

    # ── Reads ─────────────────────────────────────────────────────────────────

    def get(self, module_id: str) -> Optional[ModuleEntry]:
        return self._entries.get(module_id)

    def all(self) -> list[ModuleEntry]:
        return list(self._entries.values())

    def by_status(self, status: ModuleStatus) -> list[ModuleEntry]:
        return [e for e in self._entries.values() if e.status == status]

    def by_category(self, category: str) -> list[ModuleEntry]:
        return [e for e in self._entries.values() if e.category == category]

    # ── Aggregate helpers used by dashboard ──────────────────────────────────

    @property
    def count_total(self) -> int:
        return len(self._entries)

    @property
    def count_installed(self) -> int:
        return sum(1 for e in self._entries.values() if e.status == ModuleStatus.INSTALLED)

    @property
    def count_disabled(self) -> int:
        return sum(1 for e in self._entries.values() if e.status == ModuleStatus.DISABLED)

    @property
    def count_invalid(self) -> int:
        return sum(
            1 for e in self._entries.values()
            if e.status in (ModuleStatus.INVALID, ModuleStatus.INCOMPATIBLE)
        )

    @property
    def categories(self) -> list[str]:
        return sorted({e.category for e in self._entries.values()})


# ── Module-level singleton ────────────────────────────────────────────────────
# The registry lives for the lifetime of the process.
# Import it from here anywhere in the application:
#   from app.module_engine.registry import registry
registry = ModuleRegistry()
