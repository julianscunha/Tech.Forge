"""TTLCache genérico — Fase 12 §19.

Extraído de `app.package_manager.catalog_cache.CatalogCache` (Fase 11,
única fonte real de cache TTL do projeto até aqui) — mesma lógica,
reutilizável por qualquer módulo, não só o Catálogo.

Sem thread-safety complexa — projeto é single-process asyncio (mesma nota
da versão original).
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Generic, Optional, TypeVar

T = TypeVar("T")


class TTLCache(Generic[T]):
    """Cache em memória, por chave, com TTL. Não é fonte única de verdade
    — expira e some, nunca é a única cópia dos dados (spec §19)."""

    def __init__(self, ttl_seconds: int = 900):
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, dict] = {}  # {key: {"value": T, "fetched_at": datetime}}

    def get(self, key: str) -> Optional[T]:
        if key not in self._cache:
            return None

        entry = self._cache[key]
        if datetime.now() - entry["fetched_at"] > timedelta(seconds=self.ttl_seconds):
            del self._cache[key]
            return None

        return entry["value"]

    def set(self, key: str, value: T) -> None:
        self._cache[key] = {"value": value, "fetched_at": datetime.now()}

    def invalidate(self, key: str) -> None:
        self._cache.pop(key, None)
