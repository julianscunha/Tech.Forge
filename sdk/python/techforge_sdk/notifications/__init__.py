"""
SDK Notifications Service
==========================
Push in-app notifications from a module backend to the Core UI.

Phase 3: stores notifications in memory and exposes them via a queue
         that the Core API polls. Real-time delivery comes in Phase 4
         via Server-Sent Events.

Usage:
    from techforge_sdk import sdk

    sdk.notifications.push(
        title="Backup Complete",
        message="3 VMs backed up in 4m 12s.",
        level="success",
    )
    sdk.notifications.push(
        title="API Warning",
        message="Rate limit at 90%. Throttling requests.",
        level="warning",
    )
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal
from uuid import uuid4

logger = logging.getLogger("techforge.sdk.notifications")

NotificationLevel = Literal["info", "success", "warning", "error"]


@dataclass
class Notification:
    id: str
    module_id: str
    title: str
    message: str
    level: NotificationLevel
    timestamp: datetime
    read: bool = False


class NotificationsSDK:
    """
    In-process notification queue for one module.

    Fase 4 (spec §20 + diretriz do usuário): push() entrega a notificação
    diretamente na API do Core (POST /api/v1/notifications) para aparecer no
    bell da UI. Sem plataforma no ar, mantém na fila local (fallback).
    """

    DEFAULT_CORE_URL = "http://127.0.0.1:8000/api/v1"

    def __init__(self, module_id: str) -> None:
        self._module_id = module_id
        self._queue: list[Notification] = []
        self.core_api_url: str = self.DEFAULT_CORE_URL
        self.http_enabled: bool = True
        self.http_timeout: float = 2.0

    # ── Public API ────────────────────────────────────────────────────────────

    def push(
        self,
        title: str,
        message: str,
        level: NotificationLevel = "info",
    ) -> Notification:
        """
        Enqueue a notification for the Core UI to display.

        Args:
            title:   Short headline shown in the bell dropdown.
            message: Full description shown when the notification is expanded.
            level:   Visual severity — "info" | "success" | "warning" | "error".

        Returns:
            The created Notification record.
        """
        n = Notification(
            id=str(uuid4()),
            module_id=self._module_id,
            title=title,
            message=message,
            level=level,
            timestamp=datetime.utcnow(),
        )
        self._queue.append(n)
        log_fn = {
            "info":    logger.info,
            "success": logger.info,
            "warning": logger.warning,
            "error":   logger.error,
        }.get(level, logger.info)
        log_fn("[%s] notification [%s]: %s — %s", self._module_id, level, title, message)

        # Fase 4 §20 — deliver to Core API so it shows in the UI bell
        if self.http_enabled:
            self._deliver_to_core(n)
        return n

    def _deliver_to_core(self, notification: Notification) -> bool:
        """POST the notification to the Core. Falls back silently to the local queue."""
        import json as _json
        import urllib.request

        payload = _json.dumps({
            "level": notification.level,
            "title": notification.title,
            "message": notification.message,
            "module_id": notification.module_id,
        }).encode("utf-8")
        url = f"{self.core_api_url.rstrip('/')}/notifications"
        try:
            req = urllib.request.Request(
                url, data=payload, method="POST",
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=self.http_timeout):
                return True
        except Exception as exc:
            logger.debug("Core delivery failed for [%s], kept in local queue: %s",
                         self._module_id, exc)
            return False

    def pending(self) -> list[Notification]:
        """Return all unread notifications."""
        return [n for n in self._queue if not n.read]

    def mark_read(self, notification_id: str) -> None:
        """Mark a notification as read by its ID."""
        for n in self._queue:
            if n.id == notification_id:
                n.read = True
                return

    def clear(self) -> None:
        """Discard all notifications for this module."""
        self._queue.clear()
