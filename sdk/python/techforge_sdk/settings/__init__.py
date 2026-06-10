"""
SDK Settings Service
=====================
Per-module key-value configuration store.

Phase 3: persists to a JSON file inside the module's data directory.
Phase 4: backed by a dedicated SQLite table with type coercion and
         change history.

Usage:
    from techforge_sdk import sdk

    # Write
    sdk.settings.set("api_url", "https://api.example.com")
    sdk.settings.set("max_retries", 3)
    sdk.settings.set("feature_flags", {"export_csv": True})

    # Read
    url = sdk.settings.get("api_url", default="https://default.example.com")
    retries = sdk.settings.get("max_retries", default=5)

    # List / delete
    all_cfg = sdk.settings.all()
    sdk.settings.delete("deprecated_key")
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("techforge.sdk.settings")


class SettingsSDK:
    """
    Per-module persistent settings backed by a JSON file.
    Thread-safe for single-process use; Phase 4 will add row-level locking.
    """

    def __init__(self, module_id: str, data_dir: Optional[Path] = None) -> None:
        self._module_id = module_id
        if data_dir is None:
            data_dir = Path("modules") / "installed" / module_id / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        self._file = data_dir / "settings.json"
        self._cache: dict[str, Any] = self._load()
        logger.debug("SettingsSDK initialised for '%s': %s", module_id, self._file)

    # ── Public API ────────────────────────────────────────────────────────────

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a setting value.

        Args:
            key:     Setting name.
            default: Value to return if the key is not set.

        Returns:
            The stored value, or *default* if not found.
        """
        return self._cache.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Store a setting value. Persists immediately to disk.

        Args:
            key:   Setting name (non-empty string).
            value: Any JSON-serialisable value.
        """
        if not key:
            raise ValueError("Settings key must be a non-empty string.")
        self._cache[key] = value
        self._save()
        logger.debug("[%s] settings.set: %s=%r", self._module_id, key, value)

    def delete(self, key: str) -> None:
        """
        Remove a setting. No-op if the key does not exist.
        """
        if key in self._cache:
            del self._cache[key]
            self._save()
            logger.debug("[%s] settings.delete: %s", self._module_id, key)

    def all(self) -> dict[str, Any]:
        """Return a snapshot of all current settings."""
        return dict(self._cache)

    def reset(self) -> None:
        """
        Delete all settings for this module.
        Called by ModuleContract.uninstall() to clean up.
        """
        self._cache.clear()
        if self._file.exists():
            self._file.unlink()
        logger.info("[%s] settings reset.", self._module_id)

    # ── Persistence ───────────────────────────────────────────────────────────

    def _load(self) -> dict[str, Any]:
        if self._file.exists():
            try:
                return json.loads(self._file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                logger.warning("[%s] settings file corrupt — starting fresh.", self._module_id)
        return {}

    def _save(self) -> None:
        self._file.write_text(
            json.dumps(self._cache, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
