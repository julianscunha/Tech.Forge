"""ModuleKVStoreRow — Fase 12 §6/§7 (Module Storage API).

Uma linha por (module_id, key) — key-value simples para módulos que não
precisam de schema relacional próprio.
"""
from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ModuleKVStoreRow(Base):
    __tablename__ = "module_kv_store"

    module_id:  Mapped[str] = mapped_column(String(64), primary_key=True)
    key:        Mapped[str] = mapped_column(String(255), primary_key=True)
    value_json: Mapped[str] = mapped_column(Text, nullable=False)
