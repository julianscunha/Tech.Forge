"""Fase 15 Slice 9 — `techforge release-check` CLI (spec §36/§46).

Run:  cd cli && pytest tests/test_phase15_release_check_command.py -v
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

from techforge_cli.commands.release import release_check_cmd  # noqa: E402

READY_REPORT = {
    "version": "1.0.0",
    "ready": True,
    "checks": [{"name": "storage", "passed": True, "detail": "ok"}],
}

BLOCKED_REPORT = {
    "version": "1.0.0",
    "ready": False,
    "checks": [{"name": "storage", "passed": False, "detail": "banco indisponível"}],
}


@pytest.fixture()
def runner():
    return CliRunner()


def test_release_check_exits_zero_when_everything_passes(runner):
    with patch("techforge_cli.commands.release._get_readiness", return_value=READY_REPORT):
        result = runner.invoke(release_check_cmd, ["--skip-tests", "--skip-build"])
    assert result.exit_code == 0
    assert "READY" in result.output


def test_release_check_exits_nonzero_when_live_checks_fail(runner):
    with patch("techforge_cli.commands.release._get_readiness", return_value=BLOCKED_REPORT):
        result = runner.invoke(release_check_cmd, ["--skip-tests", "--skip-build"])
    assert result.exit_code != 0
    assert "BLOCKED" in result.output


def test_release_check_exits_nonzero_when_tests_fail(runner):
    with patch("techforge_cli.commands.release._get_readiness", return_value=READY_REPORT), \
         patch("techforge_cli.commands.release._run_backend_tests", return_value=False):
        result = runner.invoke(release_check_cmd, ["--skip-build"])
    assert result.exit_code != 0
    assert "BLOCKED" in result.output


def test_release_check_fails_when_platform_unreachable(runner):
    with patch("techforge_cli.commands.release._get_readiness", return_value=None):
        result = runner.invoke(release_check_cmd, ["--skip-tests", "--skip-build"])
    assert result.exit_code != 0
