"""EventBus unificado — Fase 14 §12.

Pub/sub in-process, síncrono, sem fila externa (spec não exige). Não
mantém histórico próprio — os sistemas que já existem (RuntimeEvent,
OperationLog, LoaderJournal) continuam sendo a fonte de leitura de cada
domínio; eles publicam aqui além de gravar no próprio buffer, e novos
consumidores (Diagnostics, Notifications) assinam o bus em vez de
inventar mais um buffer paralelo.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

logger = logging.getLogger("techforge.event_bus")


@dataclass
class Event:
    type: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def as_dict(self) -> dict[str, Any]:
        return {"type": self.type, "timestamp": self.timestamp.isoformat(), **self.payload}


Subscriber = Callable[[Event], None]


class EventBus:
    def __init__(self) -> None:
        self._subscribers: list[Subscriber] = []

    def subscribe(self, callback: Subscriber) -> None:
        self._subscribers.append(callback)

    def unsubscribe(self, callback: Subscriber) -> None:
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def publish(self, event_type: str, **payload: Any) -> Event:
        event = Event(type=event_type, payload=payload)
        for subscriber in list(self._subscribers):
            try:
                subscriber(event)
            except Exception:
                # um assinante com bug nunca pode derrubar quem publicou
                logger.exception("Subscriber failed handling event %s", event_type)
        return event


event_bus = EventBus()
