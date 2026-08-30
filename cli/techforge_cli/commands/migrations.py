"""techforge migrations — Alembic status/run CLI (Fase 12 §14/§30).

Acesso direto ao Alembic/SQLite (não via HTTP) — de propósito: precisa
funcionar mesmo com a plataforma parada (ex.: logo após clonar o repo,
antes do primeiro `techforge platform start`). O frontend, que só tem
acesso HTTP, consome `GET /api/v1/system/migrations/status` em vez disso
(mesma lógica, exposta como API — ver app/api/routes/system.py).
"""
from __future__ import annotations

import sys
from pathlib import Path

import click

from techforge_cli.console import console, print_error, print_info

_CORE_BACKEND = Path(__file__).resolve().parents[3] / "core" / "backend"
if str(_CORE_BACKEND) not in sys.path:
    sys.path.insert(0, str(_CORE_BACKEND))


@click.group("migrations")
def migrations_cmd():
    """Database migrations (Fase 12 — Alembic)."""


@migrations_cmd.command("status")
def status_cmd():
    """Show current vs head revision."""
    import sqlite3

    from app.db import migrations as db_migrations
    from app.db.database import settings

    head = db_migrations.head_revision()
    current = None
    path = settings.DATABASE_URL.split("///", 1)[-1]
    try:
        conn = sqlite3.connect(path)
        row = conn.execute("SELECT version_num FROM alembic_version").fetchone()
        current = row[0] if row else None
        conn.close()
    except sqlite3.Error:
        pass

    console.print(f"  Head:    {head}")
    console.print(f"  Current: {current or '(nenhuma migration aplicada)'}")
    if current == head:
        print_info("Banco em dia.")
    else:
        print_error("Há migrations pendentes — rode 'techforge migrations run'.")


@migrations_cmd.command("run")
def run_cmd():
    """Apply pending migrations (upgrade head)."""
    from app.db import migrations as db_migrations
    db_migrations.upgrade_head()
    print_info("Migrations aplicadas.")
