"""
TechForge SDK — Python
======================
This is the stub/skeleton for the official Python SDK used by module backends.

In Phase 2 (Module Loader), each service below will be fully implemented.
Module backends import from this package instead of accessing core internals directly.

Usage (module backend):
    from techforge_sdk import sdk

    sdk.logger.info("Module started")
    result = sdk.database.query("SELECT ...")
"""

from __future__ import annotations


class _DatabaseSDK:
    """
    Phase 2: will wrap SQLAlchemy sessions scoped to the calling module.
    Modules never touch the database directly — always via this interface.
    """
    def query(self, sql: str, *args): raise NotImplementedError("SDK Phase 2")
    def execute(self, sql: str, *args): raise NotImplementedError("SDK Phase 2")


class _StorageSDK:
    """Phase 2: isolated file storage per module under modules/installed/<id>/data/"""
    def read(self, path: str) -> bytes: raise NotImplementedError("SDK Phase 2")
    def write(self, path: str, data: bytes) -> None: raise NotImplementedError("SDK Phase 2")


class _LoggerSDK:
    """Phase 2: structured logging tagged with the calling module's ID."""
    def info(self, msg: str) -> None: print(f"[SDK:LOG] {msg}")
    def warning(self, msg: str) -> None: print(f"[SDK:WARN] {msg}")
    def error(self, msg: str) -> None: print(f"[SDK:ERROR] {msg}")


class _SettingsSDK:
    """Phase 2: per-module settings isolated from global Core settings."""
    def get(self, key: str, default=None): raise NotImplementedError("SDK Phase 2")
    def set(self, key: str, value) -> None: raise NotImplementedError("SDK Phase 2")


class _NotificationsSDK:
    """Phase 2: push notifications to the Core header bell."""
    def push(self, title: str, message: str, level: str = "info") -> None:
        raise NotImplementedError("SDK Phase 2")


class TechForgeSDK:
    database = _DatabaseSDK()
    storage = _StorageSDK()
    logger = _LoggerSDK()
    settings = _SettingsSDK()
    notifications = _NotificationsSDK()


sdk = TechForgeSDK()

__all__ = ["sdk", "TechForgeSDK"]
