from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

NotificationLevel = Literal["info", "warning", "error", "success"]


class NotificationCreate(BaseModel):
    level: NotificationLevel
    title: str = Field(min_length=1, max_length=256)
    message: Optional[str] = None
    module_id: Optional[str] = None


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    level: NotificationLevel
    title: str
    message: Optional[str]
    module_id: Optional[str]
    read: bool
    created_at: datetime


class UnreadCount(BaseModel):
    count: int


class MarkedResponse(BaseModel):
    marked: int
