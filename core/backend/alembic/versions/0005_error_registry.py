"""error_registry table

Fase 14 §19/§25 — captura automatica de erros nos pontos-chave do Core
(falha de execucao, falha de dependencia, erro de runtime).

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-30
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "error_registry" in inspector.get_table_names():
        return  # create_all já criou (instalação nova)
    op.create_table(
        "error_registry",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("module_id", sa.String(128), nullable=True),
        sa.Column("execution_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_error_registry_source", "error_registry", ["source"])
    op.create_index("ix_error_registry_module_id", "error_registry", ["module_id"])
    op.create_index("ix_error_registry_execution_id", "error_registry", ["execution_id"])
    op.create_index("ix_error_registry_created_at", "error_registry", ["created_at"])


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "error_registry" in inspector.get_table_names():
        op.drop_table("error_registry")
