"""
/api/v1/marketplace — Package Manager REST API
================================================
Exposes install, update, remove, import and listing operations to the
frontend Marketplace page.

All write operations delegate to the singleton package_manager, which
handles hot-reload of the in-memory registry automatically.
"""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from pydantic import BaseModel
from typing import Optional

from app.package_manager import (
    package_manager, operation_log,
    InstallStatus, RemoveStatus, UpdateStatus, CompatibilityLevel,
)
from app.package_manager.models import PackageInfo
from app.core.settings import settings

logger = logging.getLogger("techforge.marketplace.api")
router = APIRouter(prefix="/marketplace", tags=["marketplace"])


# ── Response models ───────────────────────────────────────────────────────────

class PackageInfoRead(BaseModel):
    module_id:   str
    name:        str
    version:     str
    category:    str
    vendor:      str
    author:      str
    description: str
    platform_min_version: str
    platform_max_version: str
    compatibility: str
    is_installed:      bool
    is_enabled:        Optional[bool] = None
    installed_version: Optional[str]
    install_date:      Optional[str]
    trust_level: str
    signature:   Optional[str]
    checksum:    Optional[str]
    publisher:   Optional[str]
    icon:        Optional[str]
    color:       Optional[str]
    order:       Optional[int]
    has_update:  bool
    homepage:    Optional[str]
    documentation: Optional[str]

    @classmethod
    def from_info(cls, p: PackageInfo) -> "PackageInfoRead":
        return cls(
            module_id   = p.module_id,
            name        = p.name,
            version     = p.version,
            category    = p.category,
            vendor      = p.vendor,
            author      = p.author,
            description = p.description,
            platform_min_version=p.platform_min_version,
            platform_max_version=p.platform_max_version,
            compatibility=p.compatibility.value,
            is_installed=p.is_installed,
            is_enabled=p.is_enabled,
            installed_version=p.installed_version,
            install_date=p.install_date.isoformat() if p.install_date else None,
            trust_level=p.trust_level.value,
            signature=p.signature,
            checksum=p.checksum,
            publisher=p.publisher,
            icon=p.icon,
            color=p.color,
            order=p.order,
            has_update=p.has_update,
            homepage=p.homepage,
            documentation=p.documentation,
        )


class OperationResponse(BaseModel):
    success:   bool
    status:    str
    module_id: str
    message:   str


class OperationLogRead(BaseModel):
    timestamp: str
    operation: str
    module_id: str
    version:   str
    status:    str
    message:   str
    details:   dict


# ── Listing endpoints ─────────────────────────────────────────────────────────

@router.get("/installed", response_model=list[PackageInfoRead])
async def list_installed():
    """Return all currently installed modules with their runtime metadata."""
    packages = await package_manager.list_installed()
    return [PackageInfoRead.from_info(p) for p in packages]


@router.get("/available", response_model=list[PackageInfoRead])
async def list_available():
    """
    Return all packages available in modules/repository/.
    Each entry is annotated with is_installed and has_update.
    """
    packages = await package_manager.list_available()
    return [PackageInfoRead.from_info(p) for p in packages]


@router.get("/updates", response_model=list[PackageInfoRead])
async def list_updates():
    """Return installed modules that have a newer version in repository/."""
    packages = await package_manager.list_updates()
    return [PackageInfoRead.from_info(p) for p in packages]


# ── Install ───────────────────────────────────────────────────────────────────

@router.post("/install/{module_id}", response_model=OperationResponse)
async def install_module(module_id: str):
    """
    Install a module from modules/repository/.

    The package_manager locates the latest .mod file for module_id
    in the repository and installs it.
    """
    mod_path = await package_manager._repo.fetch_mod_path(module_id)
    if mod_path is None:
        raise HTTPException(
            status_code=404,
            detail=f"No .mod file found for '{module_id}' in repository.",
        )

    result = await package_manager.install(mod_path)
    return OperationResponse(
        success=result.success,
        status=result.status.value,
        module_id=result.module_id,
        message=result.message,
    )


# ── Remove ────────────────────────────────────────────────────────────────────

@router.delete("/remove/{module_id}", response_model=OperationResponse)
async def remove_module(module_id: str):
    """Remove an installed module and hot-reload the registry."""
    result = await package_manager.remove(module_id)
    if result.status == RemoveStatus.NOT_FOUND:
        raise HTTPException(status_code=404, detail=result.message)
    return OperationResponse(
        success=result.success,
        status=result.status.value,
        module_id=result.module_id,
        message=result.message,
    )


# ── Update ────────────────────────────────────────────────────────────────────

@router.post("/update/{module_id}", response_model=OperationResponse)
async def update_module(module_id: str):
    """
    Update an installed module to the latest version in repository/.
    Blocked if the new version is incompatible.
    """
    mod_path = await package_manager._repo.fetch_mod_path(module_id)
    if mod_path is None:
        raise HTTPException(
            status_code=404,
            detail=f"No .mod file found for '{module_id}' in repository.",
        )

    result = await package_manager.update(module_id, mod_path)
    return OperationResponse(
        success=result.success,
        status=result.status.value,
        module_id=result.module_id,
        message=result.message,
    )


# ── Manual import ─────────────────────────────────────────────────────────────

@router.post("/import", response_model=OperationResponse)
async def import_module(file: UploadFile = File(...)):
    """
    Import a .mod file uploaded directly by the user.

    The file goes through the same full validation pipeline as a
    repository install (manifest check, compatibility, structure).
    No special trust is granted — trust_level stays UNSIGNED.
    """
    if not file.filename or not file.filename.endswith(".mod"):
        raise HTTPException(
            status_code=400,
            detail="Only .mod files are accepted for import.",
        )

    content = await file.read()

    # Store to cache/
    stored_path = await package_manager._repo.store_upload(file.filename, content)

    result = await package_manager.install(stored_path)

    # Clean up cache after install attempt
    try:
        stored_path.unlink(missing_ok=True)
    except Exception:
        pass

    return OperationResponse(
        success=result.success,
        status=result.status.value,
        module_id=result.module_id,
        message=result.message,
    )


# ── Compatibility check ───────────────────────────────────────────────────────

class CompatibilityRequest(BaseModel):
    platform_min_version: str
    platform_max_version: str

class CompatibilityResponse(BaseModel):
    platform_version: str
    level: str
    label: str

@router.post("/compatibility", response_model=CompatibilityResponse)
async def check_compat(req: CompatibilityRequest):
    """Check compatibility of a version range against the running platform."""
    from app.package_manager.compatibility import check_compatibility, format_compatibility
    level = check_compatibility(
        settings.PLATFORM_VERSION,
        req.platform_min_version,
        req.platform_max_version,
    )
    return CompatibilityResponse(
        platform_version=settings.PLATFORM_VERSION,
        level=level.value,
        label=format_compatibility(level),
    )


# ── Operation log ─────────────────────────────────────────────────────────────

@router.get("/log", response_model=list[OperationLogRead])
async def get_operation_log(limit: int = Query(50, ge=1, le=500)):
    """Return the most recent Package Manager operations."""
    return [
        OperationLogRead(
            timestamp=e.timestamp.isoformat(),
            operation=e.operation,
            module_id=e.module_id,
            version=e.version,
            status=e.status,
            message=e.message,
            details=e.details,
        )
        for e in operation_log.recent(limit)
    ]


# ── Activate / Deactivate (Fase 4 §9/§10) ────────────────────────────────────

class LifecycleResponse(BaseModel):
    success: bool
    status: str
    module_id: str
    message: str


@router.post("/activate/{module_id}", response_model=LifecycleResponse)
async def activate_module_route(module_id: str):
    """DISABLED → INSTALLED. Hot-mounts the module's backend router."""
    from app.package_manager.lifecycle import activate_module
    from app.db.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        result = await activate_module(db, module_id)
    if not result["ok"]:
        raise HTTPException(status_code=result["status"], detail=result["detail"])
    return LifecycleResponse(success=True, module_id=module_id,
                             status=result.get("status_value", "ok"),
                             message=result["message"])


@router.post("/deactivate/{module_id}", response_model=LifecycleResponse)
async def deactivate_module_route(module_id: str):
    """INSTALLED → DISABLED. Files preserved; skipped at next boot."""
    from app.package_manager.lifecycle import deactivate_module
    from app.db.database import AsyncSessionLocal
    import asyncio

    async with AsyncSessionLocal() as db:
        result = await deactivate_module(db, module_id)
    if not result["ok"]:
        raise HTTPException(status_code=result["status"], detail=result["detail"])
    return LifecycleResponse(success=True, module_id=module_id,
                             status=result.get("status_value", "ok"),
                             message=result["message"])
