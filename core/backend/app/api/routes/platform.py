from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.settings import settings
from app.db.database import get_db
from app.schemas.registry import PlatformStatus
from app.services.registry import CategoryService, ModuleService

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
    except Exception:
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
