"""Fase 17 Slice 4 — CLI: security status, trust publishers, diagnostics security.

Clientes HTTP finos sobre /api/v1/security/* — nenhuma lógica de trust
duplicada aqui (mesmo padrão de commands/diagnostics.py e module_trust.py).

Run:  cd cli && python -m pytest tests/test_phase17_security_cli.py -q
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


def test_security_cmd_has_status_subcommand():
    from techforge_cli.commands.security import security_cmd
    assert "status" in security_cmd.commands


def test_trust_cmd_has_publishers_subcommand():
    from techforge_cli.commands.module_trust import trust_cmd
    assert "publishers" in trust_cmd.commands


def test_diagnostics_cmd_has_security_subcommand():
    from techforge_cli.commands.diagnostics import diagnostics_cmd
    assert "security" in diagnostics_cmd.commands


def test_all_commands_registered_in_main_cli():
    from techforge_cli.main import cli
    assert "security" in cli.commands
