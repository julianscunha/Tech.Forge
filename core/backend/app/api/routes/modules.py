from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.registry import ModuleCreate, ModuleRead
from app.services.registry import ModuleService

router = APIRouter(prefix="/modules", tags=["modules"])


@router.get("", response_model=list[ModuleRead], summary="List registered modules")
async def list_modules(db: AsyncSession = Depends(get_db)) -> list[ModuleRead]:
    """
    Returns all registered modules with their category.
    In Phase 2, this will also include lifecycle status reported
    by each module's health_check() method.
    """
    modules = await ModuleService.get_all(db)
    return list(modules)


@router.get("/{module_id}", response_model=ModuleRead)
async def get_module(module_id: str, db: AsyncSession = Depends(get_db)) -> ModuleRead:
    module = await ModuleService.get_by_module_id(db, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found.")
    return module


@router.post("", response_model=ModuleRead, status_code=status.HTTP_201_CREATED)
async def register_module(
    payload: ModuleCreate,
    db: AsyncSession = Depends(get_db),
) -> ModuleRead:
    """
    Registers a module in the Core registry.
    In Phase 2, this endpoint will trigger install() and enable()
    lifecycle hooks on the module.
    """
    existing = await ModuleService.get_by_module_id(db, payload.module_id)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Module '{payload.module_id}' is already registered.",
        )
    return await ModuleService.create(db, payload)
