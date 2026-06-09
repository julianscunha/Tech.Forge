from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.registry import CategoryCreate, CategoryRead
from app.services.registry import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryRead], summary="List all categories")
async def list_categories(db: AsyncSession = Depends(get_db)) -> list[CategoryRead]:
    categories = await CategoryService.get_all(db)
    return list(categories)


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreate,
    db: AsyncSession = Depends(get_db),
) -> CategoryRead:
    existing = await CategoryService.get_by_slug(db, payload.slug)
    if existing:
        raise HTTPException(status_code=409, detail=f"Category '{payload.slug}' already exists.")
    return await CategoryService.create(db, payload)


@router.get("/{slug}", response_model=CategoryRead)
async def get_category(slug: str, db: AsyncSession = Depends(get_db)) -> CategoryRead:
    category = await CategoryService.get_by_slug(db, slug)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found.")
    return category
