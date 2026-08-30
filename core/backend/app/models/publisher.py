"""
Publisher Registry — Fase 10 §10/§13
========================================
Tabela SQLite nova (`publishers`) — fonte local de publishers conhecidos.
Decisão do usuário: tabela, não arquivo (consistente com o padrão
100% SQLite-first do projeto).
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Publisher(Base):
    __tablename__ = "publishers"

    id:           Mapped[str] = mapped_column(String(128), primary_key=True)
    name:         Mapped[str] = mapped_column(String(256), nullable=False)
    type:         Mapped[str] = mapped_column(String(32), nullable=False,
                                               default="LOCAL_DEVELOPMENT")
    public_key:   Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    trust_status: Mapped[str] = mapped_column(String(16), nullable=False,
                                               default="UNTRUSTED")
    # Nome de atributo Python é "extra" (nao "metadata" - reservado pelo
    # SQLAlchemy declarative), mas a coluna no banco chama-se "metadata".
    extra: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)
    created_at:   Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return f"<Publisher id={self.id!r} trust_status={self.trust_status!r}>"
