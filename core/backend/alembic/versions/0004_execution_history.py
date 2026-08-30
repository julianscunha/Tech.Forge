"""execution_history table

Fase 14 §23 — histórico de execuções de módulo (ModuleExecutionResult
nunca era persistido; agora tem uma tabela real, com retenção configurável).

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-30
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "execution_history" in inspector.get_table_names():
        return  # create_all já criou (instalação nova)
    op.create_table(
        "execution_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("execution_id", sa.String(36), nullable=False, unique=True),
        sa.Column("module_id", sa.String(128), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("duration_seconds", sa.Float(), nullable=False, server_default="0"),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_execution_history_execution_id", "execution_history", ["execution_id"])
    op.create_index("ix_execution_history_module_id", "execution_history", ["module_id"])
    op.create_index("ix_execution_history_created_at", "execution_history", ["created_at"])


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "execution_history" in inspector.get_table_names():
        op.drop_table("execution_history")
