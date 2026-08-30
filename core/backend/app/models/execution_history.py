"""ExecutionHistory — Fase 14 §23.

Uma linha por execução de módulo via service_registry.invoker.invoke() —
o ModuleExecutionResult (Fase 9) descrevia essa forma mas nunca era
persistido; esta tabela é o que faltava pra virar histórico de verdade.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ExecutionHistory(Base):
    __tablename__ = "execution_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    execution_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
    module_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False)  # SUCCESS | FAILED
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    error_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
