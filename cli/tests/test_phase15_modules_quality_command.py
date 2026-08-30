"""Fase 15 Slice 10 — `techforge modules quality|release-check` CLI (spec §46).

Run:  cd cli && pytest tests/test_phase15_modules_quality_command.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "cli"))
sys.path.insert(0, str(ROOT / "core" / "backend"))

pytestmark = pytest.mark.unit

from techforge_cli.commands.modules import modules_cmd  # noqa: E402

READY = {
    "module_id": "hello_world",
    "ready": True,
    "checks": [{"name": "status", "passed": True, "detail": "INSTALLED"}],
}
BLOCKED = {
    "module_id": "hello_world",
    "ready": False,
    "checks": [{"name": "documentation", "passed": False, "detail": "faltando: ['x']"}],
}


@pytest.fixture()
def runner():
    return CliRunner()


def test_quality_command_prints_checks_and_exits_zero_when_ready(runner):
    with patch("techforge_cli.commands.modules._core_get", return_value=READY):
        result = runner.invoke(modules_cmd, ["quality", "hello_world"])
    assert result.exit_code == 0
    assert "READY" in result.output


def test_quality_command_exits_nonzero_when_blocked(runner):
    with patch("techforge_cli.commands.modules._core_get", return_value=BLOCKED):
        result = runner.invoke(modules_cmd, ["quality", "hello_world"])
    assert result.exit_code != 0
    assert "BLOCKED" in result.output


def test_release_check_command_uses_release_readiness_endpoint(runner):
    with patch("techforge_cli.commands.modules._core_get", return_value=READY) as mock_get:
        runner.invoke(modules_cmd, ["release-check", "hello_world"])
    mock_get.assert_called_once_with("/modules/hello_world/release-readiness")
