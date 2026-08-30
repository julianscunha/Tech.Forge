"""Fase 15 Slice 7 — `techforge version` CLI (spec §24/§46).

Run:  cd cli && pytest tests/test_phase15_version_command.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "cli"))
sys.path.insert(0, str(ROOT / "core" / "backend"))

pytestmark = pytest.mark.unit

from techforge_cli.commands.version import version_cmd  # noqa: E402


@pytest.fixture()
def runner():
    return CliRunner()


def test_version_command_prints_platform_version(runner):
    from app.core.settings import settings

    result = runner.invoke(version_cmd)
    assert result.exit_code == 0
    assert settings.PLATFORM_VERSION in result.output
