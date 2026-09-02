"""Fase 18 — `techforge update` CLI (self-update via git pull).

Run:  cd cli && pytest tests/test_update_command.py -v
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from click.testing import CliRunner

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "cli"))
sys.path.insert(0, str(ROOT / "core" / "backend"))

pytestmark = pytest.mark.unit

import techforge_cli.commands.update as update_mod  # noqa: E402
from techforge_cli.commands.update import update_cmd  # noqa: E402


@pytest.fixture()
def runner():
    return CliRunner()


def _clean_status():
    return subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")


def test_update_aborts_when_not_a_git_checkout(runner, monkeypatch, tmp_path):
    monkeypatch.setattr(update_mod, "_REPO_ROOT", tmp_path)  # sem .git
    result = runner.invoke(update_cmd)
    assert result.exit_code != 0


def test_update_aborts_on_uncommitted_changes(runner, monkeypatch, tmp_path):
    (tmp_path / ".git").mkdir()
    monkeypatch.setattr(update_mod, "_REPO_ROOT", tmp_path)
    monkeypatch.setattr(update_mod, "_git", lambda *a: subprocess.CompletedProcess(
        args=[], returncode=0, stdout=" M dirty_file.py\n", stderr=""))
    result = runner.invoke(update_cmd)
    assert result.exit_code != 0


def test_update_reports_already_current_without_touching_platform(runner, monkeypatch, tmp_path):
    (tmp_path / ".git").mkdir()
    monkeypatch.setattr(update_mod, "_REPO_ROOT", tmp_path)
    monkeypatch.setattr(update_mod, "_git", lambda *a: _clean_status())

    async def fake_check_for_update():
        return SimpleNamespace(update_available=False, latest_version=None)
    monkeypatch.setattr("app.services.update_check.check_for_update", fake_check_for_update)

    launcher_calls = []
    monkeypatch.setattr(update_mod, "_run_launcher", lambda *a: launcher_calls.append(a))

    result = runner.invoke(update_cmd, ["--yes"])
    assert result.exit_code == 0
    assert launcher_calls == []


def test_update_runs_full_flow_when_newer_version_exists(runner, monkeypatch, tmp_path):
    (tmp_path / ".git").mkdir()
    monkeypatch.setattr(update_mod, "_REPO_ROOT", tmp_path)
    monkeypatch.setattr(update_mod, "_git", lambda *a: _clean_status())

    async def fake_check_for_update():
        return SimpleNamespace(update_available=True, latest_version="99.0.0")
    monkeypatch.setattr("app.services.update_check.check_for_update", fake_check_for_update)

    launcher_calls = []
    monkeypatch.setattr(update_mod, "_run_launcher", lambda *a: launcher_calls.append(a) or 0)
    # Rebind the `subprocess` name only inside update_mod — must NOT patch the
    # real subprocess module, since stdlib internals (e.g. platform.py) call
    # subprocess.run() too and would break on a stubbed CompletedProcess.
    fake_subprocess = SimpleNamespace(
        run=lambda *a, **k: subprocess.CompletedProcess(args=[], returncode=0))
    monkeypatch.setattr(update_mod, "subprocess", fake_subprocess)
    monkeypatch.setattr("app.db.migrations.upgrade_head", lambda: None)

    result = runner.invoke(update_cmd, ["--yes"])
    assert result.exit_code == 0
    assert ("stop",) in launcher_calls
    assert ("start",) in launcher_calls
