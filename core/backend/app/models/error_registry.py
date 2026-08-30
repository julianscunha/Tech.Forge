"""ErrorRecord — Fase 14 §19/§25 (Error Registry).

Uma linha por erro capturado automaticamente nos pontos-chave do Core
(falha de execução de módulo, falha de dependência, erro de runtime).
Não substitui o log — é um índice consultável dos erros que importam.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ErrorRecord(Base):
    __tablename__ = "error_registry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False, index=True)  # execution|dependency|runtime
    message: Mapped[str] = mapped_column(Text, nullable=False)
    detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    module_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    execution_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
