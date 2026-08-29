"""module_kv_store table

Fase 12 §6/§7 — Module Storage API (key-value), 1 linha por (module_id, key).

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-29
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "module_kv_store" in inspector.get_table_names():
        return  # create_all já criou (instalação nova)
    op.create_table(
        "module_kv_store",
        sa.Column("module_id", sa.String(64), primary_key=True),
        sa.Column("key", sa.String(255), primary_key=True),
        sa.Column("value_json", sa.Text(), nullable=False),
    )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "module_kv_store" in inspector.get_table_names():
        op.drop_table("module_kv_store")
