"""techforge migrations — Alembic status/run CLI (Fase 12 §14/§30).

Consome a API do Core (/api/v1/system/migrations/status) e o próprio
Alembic (upgrade head roda contra o mesmo banco do Core, mesma URL de
`app.core.settings`) — nenhuma lógica de migration duplicada aqui.
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
    from app.db import migrations as db_migrations
    from app.db.database import settings
    import sqlite3
    from urllib.parse import urlparse

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
