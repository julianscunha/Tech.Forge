"""ModuleConfiguration — Fase 12 §10.

Uma linha por módulo, valores validados serializados em JSON — não uma
tabela por módulo (spec §10, decisão confirmada com o usuário).
"""
from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ModuleConfiguration(Base):
    __tablename__ = "module_configurations"

    module_id:   Mapped[str] = mapped_column(String(64), primary_key=True)
    values_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
