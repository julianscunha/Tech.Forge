"""
/api/v1/registry — Runtime Module Registry
==========================================
These endpoints expose the in-memory ModuleRegistry to the frontend.
They are distinct from /api/v1/modules (which queries SQLite) because
the runtime registry contains live status data that may differ from the DB.
"""
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel as _BaseModel

from app.module_engine import journal as loader_journal
from app.module_engine.navigation import NavigationBuilder
from app.module_engine.registry import registry
from app.schemas.module_engine import (
    LoaderResultRead,
    ModuleEntryRead,
    RegistrySummary,
)

router = APIRouter(prefix="/registry", tags=["module-registry"])


@router.get("/summary", response_model=RegistrySummary)
async def get_registry_summary() -> RegistrySummary:
    """Aggregate counts for the dashboard and sidebar badge."""
    return RegistrySummary(
        total=registry.count_total,
        installed=registry.count_installed,
        disabled=registry.count_disabled,
        invalid=registry.count_invalid,
        categories=registry.categories,
    )


@router.get("/modules", response_model=list[ModuleEntryRead])
async def list_registry_modules(
    developer_mode: bool = Query(False, description="Include raw manifest payload"),
) -> list[ModuleEntryRead]:
    """
    List all registered modules with their runtime status.

    When developer_mode=true, the manifest_raw field is populated so the
    Developer Mode panel can display the full parsed manifest.
    """
    entries = registry.all()
    return [
        ModuleEntryRead(
            module_id=e.module_id,
            name=e.name,
            version=e.version,
            category=e.category,
            vendor=e.vendor,
            author=e.author,
            description=e.description,
            status=e.status,
            install_date=e.install_date,
            errors=e.errors,
            warnings=e.warnings,
            platform_min_version=e.platform_min_version,
            platform_max_version=e.platform_max_version,
            entry_backend=e.entry_backend,
            entry_frontend=e.entry_frontend,
            is_active=e.is_active,
            icon=e.icon,
            color=e.color,
            order=e.order,
            manifest_raw=e.manifest_raw if developer_mode else None,
        )
        for e in entries
    ]


@router.get("/modules/{module_id}", response_model=ModuleEntryRead)
async def get_registry_module(
    module_id: str,
    developer_mode: bool = Query(False),
) -> ModuleEntryRead:
    entry = registry.get(module_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"Module '{module_id}' not in registry.")
    return ModuleEntryRead(
        module_id=entry.module_id,
        name=entry.name,
        version=entry.version,
        category=entry.category,
        vendor=entry.vendor,
        author=entry.author,
        description=entry.description,
        status=entry.status,
        install_date=entry.install_date,
        errors=entry.errors,
        warnings=entry.warnings,
        platform_min_version=entry.platform_min_version,
        platform_max_version=entry.platform_max_version,
        entry_backend=entry.entry_backend,
        entry_frontend=entry.entry_frontend,
        is_active=entry.is_active,
        manifest_raw=entry.manifest_raw if developer_mode else None,
    )


@router.get("/loader/journal", response_model=LoaderResultRead)
async def get_loader_journal() -> LoaderResultRead:
    """
    Returns the journal from the most recent Module Loader scan.
    Used by the Developer Mode panel to display loading logs.
    """
    result = loader_journal.get()
    if result is None:
        raise HTTPException(status_code=404, detail="No loader scan has run yet.")
    return LoaderResultRead(
        scanned=result.scanned,
        installed=result.installed,
        disabled=result.disabled,
        invalid=result.invalid,
        incompatible=result.incompatible,
        journal=[
            {
                "timestamp": ev.timestamp,
                "module_id": ev.module_id,
                "level": ev.level,
                "message": ev.message,
                "details": ev.details,
            }
            for ev in result.journal
        ],
    )


@router.post("/rescan", summary="Fase 16 §38 — Developer Mode: force reload de módulos")
async def rescan_registry(request: Request) -> dict:
    """
    Refaz o scan de modules/installed/ sem reiniciar o processo — mesmo
    mecanismo do hot-reload pós-install/update (`PackageManager._hot_reload`),
    disparado manualmente. Depois monta o router de qualquer módulo que
    ainda não estava montado (§38: "reload" pro Developer Mode).
    """
    from app.module_engine.plugin_loader import mount_module_routers
    from app.package_manager.manager import package_manager

    await package_manager._hot_reload()
    mount_result = mount_module_routers(request.app)

    result = loader_journal.get()
    return {
        "scanned": result.scanned if result else 0,
        "installed": result.installed if result else 0,
        "invalid": result.invalid if result else 0,
        "routers_mounted": mount_result.mounted,
    }


# ── Navigation tree (§7.1) ────────────────────────────────────────────────────

class NavModuleRead(_BaseModel):
    module_id: str
    name:      str
    icon:      str
    color:     str | None
    order:     int
    path:      str
    vendor:    str
    category:  str


class NavVendorRead(_BaseModel):
    vendor:  str
    modules: list[NavModuleRead]


class NavCategoryRead(_BaseModel):
    category:      str
    total_modules: int
    vendors:       list[NavVendorRead]


class NavigationTreeRead(_BaseModel):
    total_modules: int
    categories:    list[NavCategoryRead]


@router.get("/navigation", response_model=NavigationTreeRead, summary="Auto-generated navigation tree")
async def get_navigation_tree() -> NavigationTreeRead:
    """
    Returns the complete navigation tree built from all INSTALLED modules.

    Structure: category → vendor → modules (sorted by order asc).
    Only INSTALLED modules are included (INVALID/INCOMPATIBLE are excluded).
    The frontend Sidebar consumes this endpoint to build navigation automatically
    without any manual configuration.
    """
    tree = NavigationBuilder.build()
    return NavigationTreeRead(
        total_modules=tree.total_modules,
        categories=[
            NavCategoryRead(
                category=cat.category,
                total_modules=cat.total_modules,
                vendors=[
                    NavVendorRead(
                        vendor=v.vendor,
                        modules=[
                            NavModuleRead(
                                module_id=m.module_id,
                                name=m.name,
                                icon=m.icon,
                                color=m.color,
                                order=m.order,
                                path=m.path,
                                vendor=m.vendor,
                                category=m.category,
                            )
                            for m in v.modules
                        ],
                    )
                    for v in cat.vendors
                ],
            )
            for cat in tree.categories
        ],
    )
