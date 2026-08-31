"""
/api/v1/marketplace — Package Manager REST API
================================================
Exposes install, update, remove, import and listing operations to the
frontend Marketplace page.

All write operations delegate to the singleton package_manager, which
handles hot-reload of the in-memory registry automatically.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel

from app.core.settings import settings
from app.package_manager import (
    RemoveStatus,
    operation_log,
    package_manager,
)
from app.package_manager.models import PackageInfo

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
async def remove_module(module_id: str, keep_data: bool = False):
    """Remove an installed module and hot-reload the registry.

    keep_data: preserva data/ pra ser restaurado numa reinstalação futura.
    """
    result = await package_manager.remove(module_id, keep_data=keep_data)
    if result.status == RemoveStatus.NOT_FOUND:
        raise HTTPException(status_code=404, detail=result.message)
    if result.status == RemoveStatus.BLOCKED:
        raise HTTPException(status_code=409, detail=result.message)
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
    except Exception as exc:
        logger.warning("Cache cleanup failed for %s: %s", stored_path, exc)

    return OperationResponse(
        success=result.success,
        status=result.status.value,
        module_id=result.module_id,
        message=result.message,
    )


# ── Remote installation (Fase 11 Slice 5b) ───────────────────────────────────

class RemoteInstallRequest(BaseModel):
    """Request body for remote installation."""
    source_id: Optional[str] = None


class InstallJobResponse(BaseModel):
    """Response for job status queries."""
    job_id:      str
    module_id:   str
    phase:       str
    error:       Optional[str] = None
    started_at:  str
    finished_at: Optional[str] = None


@router.post("/install-remote/{module_id}", status_code=202)
async def install_remote_module(module_id: str, request: RemoteInstallRequest):
    """
    Install a module from a remote source (official or custom catalog).

    Returns immediately with a job_id. The actual installation runs in the
    background via asyncio.create_task(). Poll GET /install-jobs/{job_id}
    to track progress.

    Phases: ACQUIRING → VALIDATING → INSTALLING → DONE|FAILED
    """
    from app.package_manager.install_job import install_job_registry

    job = install_job_registry.create(module_id)

    # Start background task without blocking the response
    asyncio.create_task(_install_remote_background(module_id, job.job_id, request.source_id))

    return {"job_id": job.job_id}


async def _resolve_remote_provider(db, module_id: str, source_id: Optional[str]):
    """
    Resolve which RepositoryProvider owns *module_id* for a remote install.

    If source_id is given, it must be a registered CUSTOM_CATALOG source.
    Otherwise, look the module up in the aggregated catalog and pick the
    provider matching its CatalogSource (OFFICIAL_CATALOG or CUSTOM_CATALOG
    — LOCAL modules never go through this remote-install path).

    Returns None if the module/source cannot be resolved.
    """
    from app.package_manager.catalog_aggregator import CatalogAggregator
    from app.package_manager.catalog_source import CatalogSource
    from app.package_manager.repository import CustomCatalogProvider
    from app.services.catalog_source import CatalogSourceService

    aggregator = CatalogAggregator()

    if source_id is not None:
        sources = await CatalogSourceService.list_all(db)
        source = next((s for s in sources if s.id == source_id), None)
        if source is None:
            return None
        return CustomCatalogProvider(repo_url=source.url)

    packages, _ = await aggregator.list_all_available(db, settings.PLATFORM_VERSION)
    pkg = next((p for p in packages if p.module_id == module_id), None)
    if pkg is None:
        return None

    if pkg.source == CatalogSource.OFFICIAL_CATALOG:
        return aggregator.official_provider
    if pkg.source == CatalogSource.CUSTOM_CATALOG and pkg.source_url:
        return CustomCatalogProvider(repo_url=pkg.source_url)
    return None


async def _notify_installation(
    db, module_id: str, level: str, title: str, message: str
) -> None:
    """Helper: create installation notification with dedupe (same title + message = skip)."""
    from app.services.notifications import NotificationService

    if not await NotificationService.exists_with_title(db, title, message=message):
        await NotificationService.create(
            db, level=level, title=title, message=message, module_id=module_id
        )


async def _install_remote_background(module_id: str, job_id: str, source_id: Optional[str]) -> None:
    """
    Background task: acquire module from remote source, validate, install.

    Phases:
      1. ACQUIRING: resolve provider + fetch_mod_path() (network)
      2. VALIDATING / INSTALLING: package_manager.install() (existing pipeline)
      3. DONE / FAILED: terminal state with optional error

    fetch_mod_path() already swallows network errors and returns None
    (Slices 2/3) — never raises. Any other exception is still caught here
    so the job always reaches a terminal state (never stuck on a poll).
    """
    from app.db.database import AsyncSessionLocal
    from app.package_manager.install_job import InstallJobPhase, install_job_registry

    try:
        install_job_registry.set_phase(job_id, InstallJobPhase.ACQUIRING)

        async with AsyncSessionLocal() as db:
            provider = await _resolve_remote_provider(db, module_id, source_id)

        if provider is None:
            install_job_registry.set_phase(
                job_id, InstallJobPhase.FAILED,
                error="Módulo não encontrado em nenhuma fonte configurada.",
            )
            async with AsyncSessionLocal() as db:
                await _notify_installation(
                    db, module_id, "error", "Falha na instalação",
                    f"{module_id}: Módulo não encontrado em nenhuma fonte configurada."
                )
            return

        mod_path = await provider.fetch_mod_path(module_id)
        if mod_path is None:
            install_job_registry.set_phase(
                job_id, InstallJobPhase.FAILED,
                error="Falha ao baixar módulo: sem conexão com a fonte.",
            )
            async with AsyncSessionLocal() as db:
                await _notify_installation(
                    db, module_id, "error", "Falha na instalação",
                    f"{module_id}: Falha ao baixar módulo: sem conexão com a fonte."
                )
            return

        install_job_registry.set_phase(job_id, InstallJobPhase.VALIDATING)
        install_job_registry.set_phase(job_id, InstallJobPhase.INSTALLING)

        # Botão "Atualizar" do Catálogo (fonte remota) manda pro mesmo job
        # de instalação — sem este branch, package_manager.install() recusa
        # com "already installed. Use update to upgrade." e o job falha
        # mesmo indo tudo bem, porque nunca havia jeito de pedir update
        # numa fonte remota (só a aba "Atualizações", que é local). Usa o
        # registry (fonte única) em vez de checar o diretório no disco —
        # uma pasta órfã/inválida não conta como "instalado de verdade".
        from app.module_engine.enums import ModuleStatus
        from app.module_engine.registry import registry
        existing_entry = registry.get(module_id)
        already_installed = (
            existing_entry is not None
            and existing_entry.status not in (ModuleStatus.INVALID, ModuleStatus.INCOMPATIBLE)
        )
        if already_installed:
            result = await package_manager.update(module_id, mod_path)
        else:
            result = await package_manager.install(mod_path)
        if not result.success:
            install_job_registry.set_phase(job_id, InstallJobPhase.FAILED, error=result.message)
            async with AsyncSessionLocal() as db:
                await _notify_installation(
                    db, module_id, "error", "Falha na instalação",
                    f"{module_id}: {result.message}"
                )
            return

        install_job_registry.set_phase(job_id, InstallJobPhase.DONE)
        async with AsyncSessionLocal() as db:
            await _notify_installation(
                db, module_id, "success", "Módulo instalado",
                f"Módulo {module_id} foi instalado com sucesso."
            )

    except Exception as exc:
        logger.error("Background install task failed for job %s (module %s): %s",
                     job_id, module_id, exc)
        install_job_registry.set_phase(
            job_id,
            InstallJobPhase.FAILED,
            error=str(exc)
        )
        async with AsyncSessionLocal() as db:
            await _notify_installation(
                db, module_id, "error", "Falha na instalação",
                f"{module_id}: {str(exc)}"
            )


@router.get("/install-jobs/{job_id}", response_model=InstallJobResponse)
async def get_install_job(job_id: str):
    """
    Poll the status of an installation job.

    Returns current phase, error (if any), and timestamps.
    Returns 404 if job_id not found.
    """
    from app.package_manager.install_job import install_job_registry

    job = install_job_registry.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Installation job '{job_id}' not found.")

    return InstallJobResponse(
        job_id=job.job_id,
        module_id=job.module_id,
        phase=job.phase.value,
        error=job.error,
        started_at=job.started_at.isoformat(),
        finished_at=job.finished_at.isoformat() if job.finished_at else None,
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
    from app.db.database import AsyncSessionLocal
    from app.package_manager.lifecycle import activate_module

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
    from app.db.database import AsyncSessionLocal
    from app.package_manager.lifecycle import deactivate_module

    async with AsyncSessionLocal() as db:
        result = await deactivate_module(db, module_id)
    if not result["ok"]:
        raise HTTPException(status_code=result["status"], detail=result["detail"])
    return LifecycleResponse(success=True, module_id=module_id,
                             status=result.get("status_value", "ok"),
                             message=result["message"])
