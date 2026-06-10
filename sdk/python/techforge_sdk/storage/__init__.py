"""
SDK Storage Service
====================
Sandboxed file storage for module backends.

Each module can read and write files inside its own isolated directory:
    modules/installed/<module_id>/data/

Modules NEVER access the file system directly — always through this SDK.
This allows the Core to enforce isolation and backup policies.

Usage:
    from techforge_sdk import sdk

    sdk.storage.write("config.json", b'{"key": "value"}')
    data = sdk.storage.read("config.json")
    files = sdk.storage.list("exports/")
    sdk.storage.delete("temp.txt")
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("techforge.sdk.storage")


class StorageSDK:
    """
    Isolated file storage scoped to a single module's data directory.
    Phase 3: fully functional — reads and writes real files.
    """

    def __init__(self, module_id: str, base_path: Optional[Path] = None) -> None:
        self._module_id = module_id
        # Default: modules/installed/<module_id>/data/
        if base_path is None:
            from pathlib import Path as _P
            base_path = _P("modules") / "installed" / module_id / "data"
        self._base = Path(base_path)
        self._base.mkdir(parents=True, exist_ok=True)
        logger.debug("StorageSDK root: %s", self._base)

    # ── Public API ────────────────────────────────────────────────────────────

    def read(self, path: str) -> bytes:
        """
        Read a file from the module's storage directory.

        Args:
            path: Relative path inside the module data directory.

        Returns:
            Raw bytes of the file.

        Raises:
            FileNotFoundError: if the file does not exist.
        """
        full = self._resolve(path)
        if not full.exists():
            raise FileNotFoundError(
                f"[{self._module_id}] Storage file not found: {path}"
            )
        logger.debug("[%s] storage.read: %s", self._module_id, path)
        return full.read_bytes()

    def write(self, path: str, data: bytes) -> None:
        """
        Write bytes to a file in the module's storage directory.
        Creates parent directories automatically.

        Args:
            path: Relative path inside the module data directory.
            data: Raw bytes to write.
        """
        full = self._resolve(path)
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_bytes(data)
        logger.debug("[%s] storage.write: %s (%d bytes)", self._module_id, path, len(data))

    def delete(self, path: str) -> None:
        """
        Delete a file from the module's storage directory.
        No-op if the file does not exist.
        """
        full = self._resolve(path)
        if full.exists():
            full.unlink()
            logger.debug("[%s] storage.delete: %s", self._module_id, path)

    def exists(self, path: str) -> bool:
        """Return True if the file exists in the module's storage directory."""
        return self._resolve(path).exists()

    def list(self, prefix: str = "") -> list[str]:
        """
        List all files under an optional prefix path.

        Args:
            prefix: Subdirectory to list. Empty string lists all files.

        Returns:
            List of relative path strings.
        """
        base = self._resolve(prefix) if prefix else self._base
        if not base.exists():
            return []
        return [
            str(p.relative_to(self._base))
            for p in base.rglob("*")
            if p.is_file()
        ]

    def read_text(self, path: str, encoding: str = "utf-8") -> str:
        """Read a text file. Convenience wrapper around read()."""
        return self.read(path).decode(encoding)

    def write_text(self, path: str, text: str, encoding: str = "utf-8") -> None:
        """Write a text file. Convenience wrapper around write()."""
        self.write(path, text.encode(encoding))

    # ── Internal ──────────────────────────────────────────────────────────────

    def _resolve(self, path: str) -> Path:
        """Resolve path relative to module base, preventing directory traversal."""
        resolved = (self._base / path).resolve()
        # Security: ensure the resolved path stays inside the module base
        try:
            resolved.relative_to(self._base.resolve())
        except ValueError:
            raise PermissionError(
                f"[{self._module_id}] Storage path escape attempt blocked: {path}"
            )
        return resolved
