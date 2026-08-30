"""
TechForge SDK — Service Contracts
===================================
All SDK services are defined here as typed interfaces.
Phase 2: stubs that raise NotImplementedError (except logger).
Phase 3+: each service will be fully implemented by the Core.

Modules import from the top-level package:
    from techforge_sdk import sdk
    sdk.logger.info("Module started")
"""
from __future__ import annotations

import logging
from abc import ABC
from typing import Any, Optional

# ── Base interface ─────────────────────────────────────────────────────────────

class SDKService(ABC):
    """Base class for all SDK services."""
    _phase: str = "2"

    def _not_implemented(self, method: str) -> None:
        raise NotImplementedError(
            f"sdk.{method} is not available in Phase {self._phase}. "
            f"It will be implemented in a later phase."
        )


# ── Database SDK ──────────────────────────────────────────────────────────────

class DatabaseSDK(SDKService):
    """
    Isolated database access for module backends.

    Phase 3: will wrap an AsyncSession scoped to the calling module's
    schema/prefix so modules cannot access each other's data.

    Contract:
        results = await sdk.database.fetch_all("SELECT * FROM my_table")
        await sdk.database.execute("INSERT INTO my_table VALUES (?)", [value])
    """

    async def fetch_all(self, query: str, params: Optional[list] = None) -> list[dict]:
        self._not_implemented("database.fetch_all")

    async def fetch_one(self, query: str, params: Optional[list] = None) -> Optional[dict]:
        self._not_implemented("database.fetch_one")

    async def execute(self, query: str, params: Optional[list] = None) -> None:
        self._not_implemented("database.execute")

    async def execute_many(self, query: str, params_list: list[list]) -> None:
        self._not_implemented("database.execute_many")


# ── Storage SDK ───────────────────────────────────────────────────────────────

class StorageSDK(SDKService):
    """
    Isolated file storage for module backends.
    Phase 3: each module gets a sandboxed directory under
    modules/installed/<module_id>/data/

    Contract:
        data = sdk.storage.read("config.json")
        sdk.storage.write("output.csv", csv_bytes)
        sdk.storage.delete("temp.txt")
        paths = sdk.storage.list("exports/")
    """

    def read(self, path: str) -> bytes:
        self._not_implemented("storage.read")

    def write(self, path: str, data: bytes) -> None:
        self._not_implemented("storage.write")

    def delete(self, path: str) -> None:
        self._not_implemented("storage.delete")

    def list(self, prefix: str = "") -> list[str]:
        self._not_implemented("storage.list")

    def exists(self, path: str) -> bool:
        self._not_implemented("storage.exists")


# ── Logger SDK ────────────────────────────────────────────────────────────────

class LoggerSDK(SDKService):
    """
    Structured logging tagged with the calling module's ID.
    Phase 2: functional — delegates to Python's logging module.
    Phase 3: will also persist to the platform log store and surface in the UI.

    Contract:
        sdk.logger.info("Processing started", extra={"count": 42})
        sdk.logger.warning("Rate limit approaching")
        sdk.logger.error("External API unreachable", exc_info=True)
    """

    def __init__(self, module_id: str = "unknown") -> None:
        self._log = logging.getLogger(f"techforge.module.{module_id}")

    def debug(self, msg: str, **kwargs: Any) -> None:
        self._log.debug(msg, **kwargs)

    def info(self, msg: str, **kwargs: Any) -> None:
        self._log.info(msg, **kwargs)

    def warning(self, msg: str, **kwargs: Any) -> None:
        self._log.warning(msg, **kwargs)

    def error(self, msg: str, **kwargs: Any) -> None:
        self._log.error(msg, **kwargs)

    def critical(self, msg: str, **kwargs: Any) -> None:
        self._log.critical(msg, **kwargs)


# ── Settings SDK ──────────────────────────────────────────────────────────────

class SettingsSDK(SDKService):
    """
    Per-module key-value configuration store.
    Phase 3: backed by a dedicated table in SQLite, isolated per module.

    Contract:
        api_key = sdk.settings.get("api_key", default="")
        sdk.settings.set("cache_ttl", 3600)
        sdk.settings.delete("deprecated_key")
        all_settings = sdk.settings.all()
    """

    def get(self, key: str, default: Any = None) -> Any:
        self._not_implemented("settings.get")

    def set(self, key: str, value: Any) -> None:
        self._not_implemented("settings.set")

    def delete(self, key: str) -> None:
        self._not_implemented("settings.delete")

    def all(self) -> dict[str, Any]:
        self._not_implemented("settings.all")


# ── Notifications SDK ─────────────────────────────────────────────────────────

class NotificationsSDK(SDKService):
    """
    Push in-app notifications to the Core header bell.
    Phase 3: will emit Server-Sent Events consumed by the frontend.

    Contract:
        sdk.notifications.push(
            title="Backup Complete",
            message="3 VMs backed up successfully.",
            level="success",
        )
    """

    def push(
        self,
        title: str,
        message: str,
        level: str = "info",  # "info" | "success" | "warning" | "error"
    ) -> None:
        self._not_implemented("notifications.push")


# ── Root SDK ──────────────────────────────────────────────────────────────────

class TechForgeSDK:
    """
    Root SDK object.  Module backends use the module-level `sdk` singleton:
        from techforge_sdk import sdk
    """

    def __init__(self, module_id: str = "unknown") -> None:
        self.database      = DatabaseSDK()
        self.storage       = StorageSDK()
        self.logger        = LoggerSDK(module_id)
        self.settings      = SettingsSDK()
        self.notifications = NotificationsSDK()
