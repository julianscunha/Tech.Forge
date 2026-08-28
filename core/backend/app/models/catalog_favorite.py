"""
Catalog Favorite — Fase 11 Slice 4.5 — Local personalization

Tabela SQLite para marcação pessoal de favoritos. Sem avaliação pública,
sem números agregados — é uma marca desta instalação apenas.
"""

from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class CatalogFavorite(Base):
    """Personal favorite marking for a module (local, no public rating)."""

    __tablename__ = "catalog_favorites"

    module_id: Mapped[str] = mapped_column(String(256), primary_key=True)
    favorited_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return f"<CatalogFavorite module_id={self.module_id!r} favorited_at={self.favorited_at!r}>"
