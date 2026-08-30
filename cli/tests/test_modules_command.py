"""Fase 3 Slice 1 — CLI `techforge modules` reutilizando o Core (spec §19).

Regra da spec: os comandos NÃO podem duplicar validação — devem usar
ManifestParser/ModuleValidator de app.module_engine.

Run:  pytest cli/tests/test_modules_command.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "sdk" / "python"))
sys.path.insert(0, str(ROOT / "cli"))
# Core engine reused by the CLI commands
sys.path.insert(0, str(ROOT / "core" / "backend"))

from techforge_cli.commands.modules import modules_cmd

pytestmark = pytest.mark.integration


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def installed_dir(tmp_path):
    """A minimal valid module directory to scan."""
    mod = tmp_path / "installed" / "demo_module"
    (mod / "backend").mkdir(parents=True)
    (mod / "frontend").mkdir(parents=True)
    (mod / "docs").mkdir(parents=True)
    (mod / "tests").mkdir(parents=True)
    (mod / "assets").mkdir(parents=True)
    (mod / "backend" / "api.py").write_text("router = None\n", encoding="utf-8")
    (mod / "frontend" / "main.js").write_text("", encoding="utf-8")
    (mod / "manifest.yaml").write_text(
        """
id: demo_module
name: Demo Module
version: 1.0.0
description: Demo
category: Examples
vendor: TechForge
author: Tester
module_type: application
entry_backend: backend/api.py
entry_frontend: frontend/main.js
icon: box
order: 10
compatibility:
  platform_min_version: "0.0.0"
""",
        encoding="utf-8",
    )
    return tmp_path / "installed"


def test_modules_list_scans_installed_dir(runner, installed_dir):
    result = runner.invoke(modules_cmd, ["list", "--modules-dir", str(installed_dir)])
    assert result.exit_code == 0, result.output
    assert "demo_module" in result.output


def test_modules_list_reports_invalid_module_without_crash(runner, installed_dir):
    bad = installed_dir / "broken_mod"
    bad.mkdir()
    (bad / "manifest.yaml").write_text("id: [unclosed\n", encoding="utf-8")
    result = runner.invoke(modules_cmd, ["list", "--modules-dir", str(installed_dir)])
    assert result.exit_code == 0  # invalid module must not crash the CLI
    assert "demo_module" in result.output
    assert "broken_mod" in result.output


def test_modules_show_prints_details(runner, installed_dir):
    result = runner.invoke(modules_cmd, ["show", "demo_module",
                                         "--modules-dir", str(installed_dir)])
    assert result.exit_code == 0, result.output
    for expected in ("Demo Module", "1.0.0", "application", "Examples"):
        assert expected in result.output


def test_modules_show_unknown_id_fails_cleanly(runner, installed_dir):
    result = runner.invoke(modules_cmd, ["show", "ghost",
                                         "--modules-dir", str(installed_dir)])
    assert result.exit_code != 0
    assert "ghost" in result.output


def test_modules_validate_uses_core_validator(runner, installed_dir):
    result = runner.invoke(modules_cmd, ["validate", str(installed_dir / "demo_module")])
    assert result.exit_code == 0, result.output
    assert "VALID" in result.output


def test_modules_validate_invalid_module_exits_nonzero(runner, installed_dir):
    bad = installed_dir / "broken_mod"
    bad.mkdir(exist_ok=True)
    (bad / "manifest.yaml").write_text("id: [unclosed\n", encoding="utf-8")
    result = runner.invoke(modules_cmd, ["validate", str(bad)])
    assert result.exit_code != 0


def test_cli_does_not_duplicate_manifest_parsing():
    """Spec §19: validation logic must come from the Core, not a CLI copy."""
    import inspect

    from techforge_cli.commands import modules as modules_src

    src = inspect.getsource(modules_src)
    # the command module must import from app.module_engine
    assert "app.module_engine" in src
    # and must not define its own required-field checks
    assert "REQUIRED_FIELDS" not in src.replace("REQUIRED_FIELDS = None", "")
