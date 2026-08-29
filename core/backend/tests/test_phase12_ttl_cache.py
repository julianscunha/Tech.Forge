"""Fase 12 Slice 8 — TTLCache genérico (spec §19).

Extraído de `app.package_manager.catalog_cache.CatalogCache` (Fase 11) —
mesma lógica, reutilizável por qualquer módulo, não só o Catálogo.

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase12_ttl_cache.py -q
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))

from app.storage.cache import TTLCache


def test_get_returns_none_on_cache_miss():
    cache = TTLCache(ttl_seconds=60)
    assert cache.get("missing") is None


def test_set_then_get_returns_value_within_ttl():
    cache = TTLCache(ttl_seconds=60)
    cache.set("k", ["a", "b"])
    assert cache.get("k") == ["a", "b"]


def test_get_returns_none_after_ttl_expires():
    cache = TTLCache(ttl_seconds=0)
    cache.set("k", "value")
    time.sleep(0.01)
    assert cache.get("k") is None


def test_invalidate_removes_entry_immediately_ignoring_ttl():
    cache = TTLCache(ttl_seconds=3600)
    cache.set("k", "value")
    cache.invalidate("k")
    assert cache.get("k") is None


def test_invalidate_on_missing_key_does_not_raise():
    cache = TTLCache(ttl_seconds=60)
    cache.invalidate("never_set")  # não deve levantar


def test_is_generic_over_any_value_type():
    cache: TTLCache[dict] = TTLCache(ttl_seconds=60)
    cache.set("k", {"nested": [1, 2, 3]})
    assert cache.get("k") == {"nested": [1, 2, 3]}
