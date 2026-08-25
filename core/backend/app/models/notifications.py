from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Boolean, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Notification(Base):
    """
    Core notification (Fase 2, spec §10/§13).

    Simple platform-level notification with a severity level.
    The Core DB may own notifications — they are platform data,
    never module business data.
    """
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    level: Mapped[str] = mapped_column(String(16), nullable=False, index=True)  # info|warning|error|success
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    module_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return f"<Notification level={self.level!r} title={self.title!r}>"
