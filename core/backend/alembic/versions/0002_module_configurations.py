"""module_configurations table

Fase 12 §10/§12 — persiste valores de configuração validados por módulo,
1 linha por módulo (não 1 tabela por módulo).

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-29
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "module_configurations" in inspector.get_table_names():
        return  # create_all já criou (instalação nova)
    op.create_table(
        "module_configurations",
        sa.Column("module_id", sa.String(64), primary_key=True),
        sa.Column("values_json", sa.Text(), nullable=False, server_default="{}"),
    )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "module_configurations" in inspector.get_table_names():
        op.drop_table("module_configurations")
