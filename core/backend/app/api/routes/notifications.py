
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.notifications import (
    MarkedResponse,
    NotificationCreate,
    NotificationRead,
    UnreadCount,
)
from app.services.notifications import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationRead])
async def list_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
) -> list[NotificationRead]:
    """List notifications, newest first (Fase 2 §10)."""
    items = await NotificationService.list(db, unread_only=unread_only, limit=limit)
    return [NotificationRead.model_validate(n) for n in items]


@router.post("", response_model=NotificationRead, status_code=201)
async def create_notification(
    payload: NotificationCreate, db: AsyncSession = Depends(get_db)
) -> NotificationRead:
    notification = await NotificationService.create(
        db,
        level=payload.level,
        title=payload.title,
        message=payload.message,
        module_id=payload.module_id,
    )
    return NotificationRead.model_validate(notification)


@router.get("/unread-count", response_model=UnreadCount)
async def unread_count(db: AsyncSession = Depends(get_db)) -> UnreadCount:
    return UnreadCount(count=await NotificationService.count_unread(db))


@router.post("/read-all", response_model=MarkedResponse)
async def read_all(db: AsyncSession = Depends(get_db)) -> MarkedResponse:
    return MarkedResponse(marked=await NotificationService.mark_all_read(db))


@router.post("/{notification_id}/read", response_model=NotificationRead)
async def mark_read(
    notification_id: int, db: AsyncSession = Depends(get_db)
) -> NotificationRead:
    ok = await NotificationService.mark_read(db, notification_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Notification not found")
    # re-fetch to return the updated entity
    from sqlalchemy import select

    from app.models.notifications import Notification

    result = await db.execute(
        select(Notification).where(Notification.id == notification_id)
    )
    return NotificationRead.model_validate(result.scalar_one())
