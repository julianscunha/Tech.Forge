"""
Catalog Source Configuration — Fase 11 Slice 4 §18/§19

Tabela SQLite para fontes de catálogo customizadas configuradas pelo usuário.
Mesmo padrão de app/models/publisher.py (Fase 10).
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.package_manager.catalog_source import CatalogSource


class CatalogSourceConfig(Base):
    """User-configured catalog source (custom or official)."""

    __tablename__ = "catalog_sources"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    url: Mapped[str] = mapped_column(String(512), nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return f"<CatalogSourceConfig id={self.id!r} name={self.name!r} type={self.type!r} enabled={self.enabled}>"
