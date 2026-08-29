"""baseline — modules.source_type / modules.source_location

Fase 12 §14: primeira revisão Alembic, substitui a whitelist ad-hoc que
existia em `app.db.database._migrate()` (adicionada na Fase 11 para
instalações antigas cujo arquivo SQLite foi criado antes de
`source_type`/`source_location` existirem no modelo `Module`).

Instalação nova: `Base.metadata.create_all()` já cria a tabela `modules`
com essas colunas — por isso os `add_column` aqui checam a existência da
coluna antes de agir, exatamente como o código antigo fazia.

Revision ID: 0001
Revises:
Create Date: 2026-08-29
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def _existing_columns(table: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table not in inspector.get_table_names():
        return set()
    return {col["name"] for col in inspector.get_columns(table)}


def upgrade() -> None:
    existing = _existing_columns("modules")
    if not existing:
        # Tabela ainda não existe (create_all() roda antes da migration na
        # inicialização) — nada a fazer, a tabela já nasce completa.
        return
    with op.batch_alter_table("modules") as batch:
        if "source_type" not in existing:
            batch.add_column(sa.Column("source_type", sa.String(16), nullable=False, server_default="local"))
        if "source_location" not in existing:
            batch.add_column(sa.Column("source_location", sa.String(512), nullable=True))


def downgrade() -> None:
    existing = _existing_columns("modules")
    with op.batch_alter_table("modules") as batch:
        if "source_location" in existing:
            batch.drop_column("source_location")
        if "source_type" in existing:
            batch.drop_column("source_type")
