"""
Package Manager Operation Log
================================
Records every install / update / remove / failure event in memory.
Phase 5: persisted to SQLite for the Notification Center and audit trail.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.observability.events import event_bus

logger = logging.getLogger("techforge.pkg_log")


@dataclass
class OperationLogEntry:
    timestamp:   datetime
    operation:   str          # "install" | "update" | "remove" | "validate" | "import"
    module_id:   str
    version:     str
    status:      str          # "success" | "failed" | "incompatible" | ...
    message:     str
    details:     dict = field(default_factory=dict)


class OperationLog:
    """In-process ring buffer of Package Manager events."""

    MAX_ENTRIES = 500

    def __init__(self) -> None:
        self._entries: list[OperationLogEntry] = []

    def record(
        self,
        operation: str,
        module_id: str,
        version:   str,
        status:    str,
        message:   str,
        **details,
    ) -> None:
        entry = OperationLogEntry(
            timestamp=datetime.now(timezone.utc),
            operation=operation,
            module_id=module_id,
            version=version,
            status=status,
            message=message,
            details=details,
        )
        self._entries.append(entry)
        if len(self._entries) > self.MAX_ENTRIES:
            self._entries = self._entries[-self.MAX_ENTRIES:]

        event_bus.publish(f"package_manager.{operation}", module_id=module_id,
                          version=version, status=status, message=message, **details)

        log_fn = logger.error if status == "failed" else logger.info
        log_fn("[pkg:%s] %s %s v%s — %s", operation, status, module_id, version, message)

    def all(self) -> list[OperationLogEntry]:
        return list(reversed(self._entries))

    def for_module(self, module_id: str) -> list[OperationLogEntry]:
        return [e for e in reversed(self._entries) if e.module_id == module_id]

    def recent(self, n: int = 50) -> list[OperationLogEntry]:
        return list(reversed(self._entries))[:n]


# Module-level singleton
operation_log = OperationLog()
