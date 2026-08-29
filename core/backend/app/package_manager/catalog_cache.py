"""
Catalog Cache — Fase 11 Slice 4 §18

In-memory cache with TTL per catalog source. One entry per source_id,
stores list[PackageInfo] + fetched_at timestamp.

Fase 12 §19: lógica genérica extraída para `app.storage.cache.TTLCache` —
esta classe fica só como alias de compatibilidade com a API já usada por
`CatalogAggregator` e pelos testes da Fase 11 (mesmo construtor, mesmos
métodos get/set/invalidate).
"""
from app.storage.cache import TTLCache
from app.package_manager.models import PackageInfo


class CatalogCache(TTLCache[list[PackageInfo]]):
    """Compat da Fase 11 — ver app.storage.cache.TTLCache pela lógica real."""


# Singleton instance
catalog_cache = CatalogCache()
