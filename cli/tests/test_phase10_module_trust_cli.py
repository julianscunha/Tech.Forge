"""Fase 10 — CLI: verify-module, integrity check, publishers list/show."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


def test_verify_module_cmd_registered():
    from techforge_cli.commands.module_trust import verify_module_cmd
    assert verify_module_cmd.name == "verify-module"


def test_integrity_cmd_has_check_subcommand():
    from techforge_cli.commands.module_trust import integrity_cmd
    assert "check" in integrity_cmd.commands


def test_publishers_cmd_has_list_and_show_subcommands():
    from techforge_cli.commands.module_trust import publishers_cmd
    assert "list" in publishers_cmd.commands
    assert "show" in publishers_cmd.commands


def test_all_commands_registered_in_main_cli():
    from techforge_cli.main import cli
    assert "verify-module" in cli.commands
    assert "integrity" in cli.commands
    assert "publishers" in cli.commands
