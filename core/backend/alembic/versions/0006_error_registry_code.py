"""error_registry.code column

Fase 14 §20 — Diagnostic Codes: cada ErrorRecord ganha um codigo estavel
(TF-EXECUTION-001 etc.) resolvido a partir da origem (source) do erro.

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-30
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {c["name"] for c in inspector.get_columns("error_registry")}
    if "code" in columns:
        return  # create_all já criou (instalação nova)
    op.add_column("error_registry", sa.Column("code", sa.String(32), nullable=True))
    op.create_index("ix_error_registry_code", "error_registry", ["code"])


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {c["name"] for c in inspector.get_columns("error_registry")}
    if "code" in columns:
        op.drop_column("error_registry", "code")
