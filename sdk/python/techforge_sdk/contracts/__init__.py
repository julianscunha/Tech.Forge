"""
TechForge SDK — Module Contracts
==================================
Base abstract classes that define the mandatory interface every TechForge
module must implement.

Module backends inherit from ModuleContract:

    from techforge_sdk.contracts import ModuleContract

    class MyModule(ModuleContract):
        async def install(self) -> None: ...
        async def enable(self)  -> None: ...
        ...
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


# ── Module metadata contract ──────────────────────────────────────────────────

@dataclass
class ModuleMetadata:
    """
    Static identity information about a module.
    Mirrors the fields declared in manifest.yaml so the Core can
    introspect a module without reading the file system.
    """
    id: str
    name: str
    version: str
    category: str
    vendor: str
    author: str
    description: str
    platform_min_version: str = "1.0.0"
    platform_max_version: str = "999.999.999"


# ── Health result ─────────────────────────────────────────────────────────────

@dataclass
class HealthResult:
    """Returned by health_check()."""
    is_healthy: bool
    message: str = "OK"
    details: dict[str, Any] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.details is None:
            self.details = {}

    @classmethod
    def ok(cls, message: str = "OK", **details: Any) -> "HealthResult":
        return cls(is_healthy=True, message=message, details=dict(details))

    @classmethod
    def fail(cls, message: str, **details: Any) -> "HealthResult":
        return cls(is_healthy=False, message=message, details=dict(details))


# ── Core module contract ──────────────────────────────────────────────────────

class ModuleContract(ABC):
    """
    Abstract base class for all TechForge module backends.

    Every module MUST subclass this and implement every abstract method.
    The Platform Loader calls these methods during the module lifecycle.

    Lifecycle order:
        install() → enable() → [running] → disable() → uninstall()
        upgrade(from_version) can be called while the module is enabled.
    """

    @property
    @abstractmethod
    def metadata(self) -> ModuleMetadata:
        """
        Return the module's static identity information.
        Must match the values in manifest.yaml exactly.
        """

    @abstractmethod
    async def install(self) -> None:
        """
        Called once when the module is first installed.
        Create database tables, default settings, initial data.
        Must be idempotent — safe to call multiple times.
        """

    @abstractmethod
    async def enable(self) -> None:
        """
        Called when the module is enabled (after install, or after disable).
        Start background tasks, open connections, register routes.
        """

    @abstractmethod
    async def disable(self) -> None:
        """
        Called when the module is disabled.
        Stop background tasks, release connections.
        Do NOT delete persistent data.
        """

    @abstractmethod
    async def upgrade(self, from_version: str) -> None:
        """
        Called when upgrading from a previous version.
        Run migrations, transform stored data, update settings schema.

        Args:
            from_version: The version string of the previously installed release.
        """

    @abstractmethod
    async def health_check(self) -> HealthResult:
        """
        Return the current health state of the module.
        Called periodically by the Core health monitor (Phase 5).

        Returns:
            HealthResult — use HealthResult.ok() or HealthResult.fail().
        """

    @abstractmethod
    async def uninstall(self) -> None:
        """
        Called when the module is permanently removed.
        Delete all data, tables, files owned by this module.
        This action is irreversible.
        """
