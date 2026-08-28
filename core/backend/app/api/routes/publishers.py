"""
/api/v1/publishers — Publisher Registry (Fase 10 §10/§13/§24)
==================================================================
Somente consulta nesta fase — registro/escrita de publisher é
interno/CLI (o Core não expõe um endpoint público de escrita de
identidade ainda).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.publisher import PublisherRead
from app.services.publisher import PublisherService

router = APIRouter(prefix="/publishers", tags=["publishers"])


@router.get("", response_model=list[PublisherRead], summary="List known publishers")
async def list_publishers(db: AsyncSession = Depends(get_db)) -> list[PublisherRead]:
    return await PublisherService.get_all(db)


@router.get("/{publisher_id}", response_model=PublisherRead, summary="Get one publisher")
async def get_publisher(publisher_id: str, db: AsyncSession = Depends(get_db)) -> PublisherRead:
    publisher = await PublisherService.get_by_id(db, publisher_id)
    if publisher is None:
        raise HTTPException(404, f"Publisher not found: {publisher_id!r}")
    return publisher
