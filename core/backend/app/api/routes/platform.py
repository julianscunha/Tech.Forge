import logging

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.db.database import get_db
from app.runtime import RuntimeState, runtime
from app.schemas.registry import PlatformHealthCheck, PlatformStatus
from app.services.registry import CategoryService, ModuleService

logger = logging.getLogger("techforge.platform.api")

router = APIRouter(prefix="/platform", tags=["platform"])


@router.get("/status", response_model=PlatformStatus, summary="Platform health and counters")
async def get_platform_status(db: AsyncSession = Depends(get_db)) -> PlatformStatus:
    """
    Returns the current health state of the platform.
    This is the primary data source for the Core dashboard (Phase 1).
    """
    # Probe database connectivity
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:
        logger.error("Database connectivity probe failed: %s", exc)
        db_status = "error"

    modules_installed = await ModuleService.count_installed(db)
    modules_enabled = await ModuleService.count_enabled(db)
    categories = await CategoryService.count(db)

    return PlatformStatus(
        platform_name=settings.PLATFORM_NAME,
        platform_version=settings.PLATFORM_VERSION,
        backend_status="online",
        database_status=db_status,
        modules_installed=modules_installed,
        modules_enabled=modules_enabled,
        categories_registered=categories,
    )


@router.get("/health", response_model=PlatformHealthCheck, summary="Spec Phase 1 health check")
async def get_platform_health_check(db: AsyncSession = Depends(get_db)) -> PlatformHealthCheck:
    """
    Health check mínimo da Fase 1 (docs/phases/01 §5):
    status + nome da plataforma + versão. Usado pelo Launcher.
    """
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:
        logger.error("Database connectivity probe failed: %s", exc)
        db_status = "error"

    return PlatformHealthCheck(
        status="ok",
        platform=settings.PLATFORM_NAME,
        version=settings.PLATFORM_VERSION,
        database=db_status,
    )


@router.get("/ready", summary="Fase 16 §15/§42 — readiness probe for the Launcher")
async def get_platform_ready(response: Response) -> dict:
    """
    Distinto de /health (que só confirma "o processo responde"): /ready só
    fica 200 depois que o boot completo (DB + Module Loader + Service
    Registry) terminou — RuntimeState.READY. O Launcher usa isto pra saber
    quando é seguro abrir a interface (spec §5: "Não abrir a interface
    antes do backend estar pronto").
    """
    ready = runtime.state is RuntimeState.READY
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"ready": ready, "state": runtime.state.value}
