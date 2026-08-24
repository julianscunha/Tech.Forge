"""
LoaderJournal
=============
Simple process-lifetime store for the most recent ModuleLoader scan result.
The Developer Mode UI queries this to display the loading log.

Phase 3 extension: replace with a persistent ring-buffer backed by SQLite
when the Marketplace requires install/upgrade history.
"""
from __future__ import annotations

from typing import Optional
from app.module_engine.loader import LoaderResult

_last_result: Optional[LoaderResult] = None


def store(result: LoaderResult) -> None:
    global _last_result
    _last_result = result


def get() -> Optional[LoaderResult]:
    return _last_result


def add_event(
    message: str,
    level: str = "info",
    module_id: Optional[str] = None,
    details: Optional[dict] = None,
) -> None:
    """Append a single event to the stored result (used by the Plugin Loader)."""
    if _last_result is not None:
        _last_result.add_event(message, level=level, module_id=module_id, details=details)
