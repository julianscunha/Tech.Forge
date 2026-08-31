"""
/api/v1/catalog/* — Module Catalog REST API
=============================================
Fase 11 Slice 5a — Server-side filtering, pagination, search, and favorite management.

All catalog operations read from CatalogAggregator (which handles multi-source caching).
Filtering, sorting, and pagination happen on the aggregated list in Python (simple,
in-memory filter/sorted/slice over what's already cached — no external search engine needed).
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.db.database import get_db
from app.package_manager.catalog_aggregator import CatalogAggregator
from app.package_manager.catalog_source import CatalogSource
from app.package_manager.models import PackageInfo
from app.services.catalog_favorite import CatalogFavoriteService
from app.services.catalog_source import CatalogSourceService

logger = logging.getLogger("techforge.catalog.api")
router = APIRouter(prefix="/catalog", tags=["catalog"])


# ── Response models ───────────────────────────────────────────────────────────

class CatalogModuleRead(BaseModel):
    """Module in catalog listing."""

    module_id: str
    name: str
    version: str
    category: str
    vendor: str
    author: str
    description: str
    platform_min_version: str
    platform_max_version: str
    compatibility: str
    trust_level: str
    is_installed: bool
    installed_version: Optional[str] = None
    install_date: Optional[str] = None
    has_update: bool
    source: str  # "local", "official_catalog", "custom_catalog"
    source_url: Optional[str] = None
    signature: Optional[str] = None
    checksum: Optional[str] = None
    publisher: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    homepage: Optional[str] = None
    documentation: Optional[str] = None
    favorite: bool  # True if in user's favorites

    @classmethod
    def from_package_info(cls, p: PackageInfo, is_favorite: bool = False) -> "CatalogModuleRead":
        return cls(
            module_id=p.module_id,
            name=p.name,
            version=p.version,
            category=p.category,
            vendor=p.vendor,
            author=p.author,
            description=p.description,
            platform_min_version=p.platform_min_version,
            platform_max_version=p.platform_max_version,
            compatibility=p.compatibility.value,
            trust_level=p.trust_level.value,
            is_installed=p.is_installed,
            installed_version=p.installed_version,
            install_date=p.install_date.isoformat() if p.install_date else None,
            has_update=p.has_update,
            source=p.source.value,
            source_url=p.source_url,
            signature=p.signature,
            checksum=p.checksum,
            publisher=p.publisher,
            icon=p.icon,
            color=p.color,
            homepage=p.homepage,
            documentation=p.documentation,
            favorite=is_favorite,
        )


class CatalogModuleListResponse(BaseModel):
    """Paginated list of modules."""

    items: list[CatalogModuleRead]
    total: int
    page: int
    page_size: int
    conflicts: dict[str, list[str]] = {}  # module_id -> list of source strings


class CatalogCategoryRead(BaseModel):
    """Category with module count."""

    name: str
    count: int


class CatalogSourceRead(BaseModel):
    """Catalog source configuration."""

    id: str
    name: str
    url: str
    type: str  # "official_catalog" or "custom_catalog"
    enabled: bool
    status: str = "available"  # "available" or "unavailable"


class CatalogSourceWrite(BaseModel):
    """Create/update catalog source."""

    name: str
    url: str
    type: str  # "official_catalog" or "custom_catalog"


# ──────────────────────────────────────────────────────────────────────────────
# GET /catalog/modules — List with filtering, sorting, pagination
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/modules", response_model=CatalogModuleListResponse, summary="List catalog modules with filtering")
async def list_catalog_modules(
    search: Optional[str] = None,
    category: Optional[str] = None,
    source: Optional[str] = None,
    trust_level: Optional[str] = None,
    compatible_only: bool = False,
    installed_only: bool = False,
    favorites_only: bool = False,
    sort: str = "name",  # "name" or "recent"
    page: int = 1,
    page_size: int = 24,
    force_refresh: bool = False,
    db: AsyncSession = Depends(get_db),
) -> CatalogModuleListResponse:
    """
    List catalog modules with server-side filtering and pagination.

    All filters are applied as AND (not OR). Pagination is on the final filtered result.
    `force_refresh=true` bypasses the aggregator's cache (TTL 900s) — usado
    pelo botão "Atualizar" da UI, senão um módulo recém-publicado no
    catálogo oficial só aparece até 15 minutos depois.
    """
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 24

    # Get all available packages from aggregator
    aggregator = CatalogAggregator()
    packages, conflicts = await aggregator.list_all_available(
        db, settings.PLATFORM_VERSION, force_refresh=force_refresh
    )

    # Get user's favorites
    favorites = await CatalogFavoriteService.list_ids(db)

    # Filter
    filtered = packages

    # Search (case-insensitive in name and description)
    if search:
        search_lower = search.lower()
        filtered = [
            p for p in filtered
            if search_lower in p.name.lower() or search_lower in p.description.lower()
        ]

    # Category
    if category:
        filtered = [p for p in filtered if p.category == category]

    # Source
    if source:
        filtered = [p for p in filtered if p.source.value == source]

    # Trust level
    if trust_level:
        filtered = [p for p in filtered if p.trust_level.value == trust_level]

    # Compatible only
    if compatible_only:
        filtered = [p for p in filtered if p.is_compatible]

    # Installed only
    if installed_only:
        filtered = [p for p in filtered if p.is_installed]

    # Favorites only
    if favorites_only:
        filtered = [p for p in filtered if p.module_id in favorites]

    # Sort
    if sort == "recent":
        # Recent = by install_date (newest first) if installed, else maintain order
        filtered = sorted(
            filtered, key=lambda p: p.install_date or datetime.min, reverse=True
        )
    else:  # "name" (default)
        filtered = sorted(filtered, key=lambda p: p.name)

    # Total count (before pagination)
    total = len(filtered)

    # Paginate
    start = (page - 1) * page_size
    end = start + page_size
    paginated = filtered[start:end]

    # Convert to response models with favorite flag
    items = [
        CatalogModuleRead.from_package_info(p, is_favorite=p.module_id in favorites)
        for p in paginated
    ]

    # Prepare conflicts response (module_id -> list of source values)
    conflicts_response = {}
    for module_id, conflict_packages in conflicts.items():
        conflicts_response[module_id] = [p.source.value for p in conflict_packages]

    return CatalogModuleListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        conflicts=conflicts_response,
    )


# ──────────────────────────────────────────────────────────────────────────────
# GET /catalog/categories — List all categories with counts
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/categories", response_model=list[CatalogCategoryRead], summary="List all categories")
async def list_catalog_categories(
    db: AsyncSession = Depends(get_db),
) -> list[CatalogCategoryRead]:
    """Get all categories with module counts (computed from aggregated packages)."""
    aggregator = CatalogAggregator()
    packages, _ = await aggregator.list_all_available(db, settings.PLATFORM_VERSION)

    # Count by category
    category_counts: dict[str, int] = {}
    for p in packages:
        category_counts[p.category] = category_counts.get(p.category, 0) + 1

    # Convert to response, sorted by name
    result = sorted(
        [CatalogCategoryRead(name=cat, count=count) for cat, count in category_counts.items()],
        key=lambda c: c.name,
    )
    return result


# ──────────────────────────────────────────────────────────────────────────────
# GET /catalog/modules/{module_id} — Get module detail
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/modules/{module_id}", response_model=CatalogModuleRead, summary="Get module details")
async def get_catalog_module_detail(
    module_id: str,
    db: AsyncSession = Depends(get_db),
) -> CatalogModuleRead:
    """Get full details of a single module from the catalog."""
    aggregator = CatalogAggregator()
    packages, _ = await aggregator.list_all_available(db, settings.PLATFORM_VERSION)

    # Find the module
    for p in packages:
        if p.module_id == module_id:
            favorites = await CatalogFavoriteService.list_ids(db)
            is_favorite = module_id in favorites
            return CatalogModuleRead.from_package_info(p, is_favorite=is_favorite)

    raise HTTPException(status_code=404, detail=f"Module not found: {module_id}")


# ──────────────────────────────────────────────────────────────────────────────
# GET /catalog/sources — List configured sources
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/sources", response_model=list[CatalogSourceRead], summary="List catalog sources")
async def list_catalog_sources(
    db: AsyncSession = Depends(get_db),
) -> list[CatalogSourceRead]:
    """List all configured catalog sources with their status."""
    sources = await CatalogSourceService.list_all(db)

    # ponytail: status is mocked as "available" for now (no actual health check)
    # add when: need to distinguish truly unavailable sources (timeout, 404, etc)
    result = [
        CatalogSourceRead(
            id=s.id,
            name=s.name,
            url=s.url,
            type=s.type,
            enabled=s.enabled,
            status="available",  # TODO: check actual availability
        )
        for s in sources
    ]
    return result


# ──────────────────────────────────────────────────────────────────────────────
# POST /catalog/sources — Add a source
# ──────────────────────────────────────────────────────────────────────────────


@router.post("/sources", response_model=CatalogSourceRead, status_code=201, summary="Add a catalog source")
async def add_catalog_source(
    payload: CatalogSourceWrite,
    db: AsyncSession = Depends(get_db),
) -> CatalogSourceRead:
    """Add a new custom catalog source."""
    # Map type string to enum
    try:
        source_type = CatalogSource[payload.type.upper()]
    except KeyError:
        raise HTTPException(400, f"Invalid source type: {payload.type}")

    source = await CatalogSourceService.add(
        db,
        name=payload.name,
        url=payload.url,
        source_type=source_type,
    )

    return CatalogSourceRead(
        id=source.id,
        name=source.name,
        url=source.url,
        type=source.type,
        enabled=source.enabled,
        status="available",
    )


# ──────────────────────────────────────────────────────────────────────────────
# DELETE /catalog/sources/{source_id} — Remove a source
# ──────────────────────────────────────────────────────────────────────────────


@router.delete("/sources/{source_id}", summary="Remove a catalog source")
async def delete_catalog_source(
    source_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Remove a catalog source by id."""
    removed = await CatalogSourceService.remove(db, source_id)
    if not removed:
        raise HTTPException(status_code=404, detail=f"Source not found: {source_id}")
    return {"success": True}


# ──────────────────────────────────────────────────────────────────────────────
# GET /catalog/updates — List modules with updates available
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/updates", response_model=CatalogModuleListResponse, summary="List modules with updates")
async def list_catalog_updates(
    page: int = 1,
    page_size: int = 24,
    db: AsyncSession = Depends(get_db),
) -> CatalogModuleListResponse:
    """List modules that have an update available (has_update=True)."""
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 24

    aggregator = CatalogAggregator()
    packages, conflicts = await aggregator.list_all_available(db, settings.PLATFORM_VERSION)

    # Filter to only those with updates
    updates = [p for p in packages if p.has_update]

    # Sort by name
    updates = sorted(updates, key=lambda p: p.name)

    # Total
    total = len(updates)

    # Paginate
    start = (page - 1) * page_size
    end = start + page_size
    paginated = updates[start:end]

    # Get favorites
    favorites = await CatalogFavoriteService.list_ids(db)

    # Convert
    items = [
        CatalogModuleRead.from_package_info(p, is_favorite=p.module_id in favorites)
        for p in paginated
    ]

    # Conflicts
    conflicts_response = {}
    for module_id, conflict_packages in conflicts.items():
        conflicts_response[module_id] = [p.source.value for p in conflict_packages]

    return CatalogModuleListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        conflicts=conflicts_response,
    )


# ──────────────────────────────────────────────────────────────────────────────
# POST /catalog/favorites/{module_id} — Add favorite
# ──────────────────────────────────────────────────────────────────────────────


@router.post("/favorites/{module_id}", summary="Add module to favorites")
async def add_favorite(
    module_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Add a module to the user's favorites."""
    await CatalogFavoriteService.add(db, module_id)
    return {"success": True}


# ──────────────────────────────────────────────────────────────────────────────
# DELETE /catalog/favorites/{module_id} — Remove favorite
# ──────────────────────────────────────────────────────────────────────────────


@router.delete("/favorites/{module_id}", summary="Remove module from favorites")
async def remove_favorite(
    module_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Remove a module from the user's favorites."""
    removed = await CatalogFavoriteService.remove(db, module_id)
    if not removed:
        raise HTTPException(status_code=404, detail=f"Module not in favorites: {module_id}")
    return {"success": True}


# ──────────────────────────────────────────────────────────────────────────────
# GET /catalog/favorites — List favorite module IDs
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/favorites", response_model=list[str], summary="List favorited module IDs")
async def list_favorites(
    db: AsyncSession = Depends(get_db),
) -> list[str]:
    """Get list of module IDs that are marked as favorites."""
    favorites = await CatalogFavoriteService.list_ids(db)
    return sorted(list(favorites))
