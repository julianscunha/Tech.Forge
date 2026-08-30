"""Fase 6 Slice 2 — `techforge logs` + modo dev (spec §16/§17).

Run:  cd D:/Github/Tech.Forge && core/backend/.venv/Scripts/python.exe -m pytest cli/tests/test_phase6_logs_dev.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "cli"))

from techforge_cli.commands.platform import logs_cmd, dev_cmd

pytestmark = pytest.mark.integration


def test_logs_shows_last_lines(tmp_path, monkeypatch):
    """logs lê o arquivo e imprime as últimas N linhas."""
    log = tmp_path / "backend.log"
    log.write_text("\n".join(f"line-{i}" for i in range(1, 21)) + "\n", encoding="utf-8")

    monkeypatch.setattr("techforge_cli.commands.platform._log_path", lambda name: log)

    result = CliRunner().invoke(logs_cmd, ["--backend", "-n", "5"])
    assert result.exit_code == 0
    lines = result.output.strip().splitlines()
    assert len(lines) == 5
    assert lines[-1] == "line-20"


def test_logs_missing_file_friendly_error(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "techforge_cli.commands.platform._log_path",
        lambda name: tmp_path / "nao_existe.log")
    result = CliRunner().invoke(logs_cmd, ["--backend"])
    assert result.exit_code == 1
    assert "nenhum log" in result.output.lower()


def test_logs_requires_one_source():
    """Nenhuma flag de origem → erro de uso."""
    result = CliRunner().invoke(logs_cmd, [])
    assert result.exit_code != 0


def test_dev_delegates_to_launcher(monkeypatch):
    """techforge dev invoca o launcher com o argumento 'dev'."""
    calls: list[list[str]] = []

    def fake_run(*args, **kwargs):
        calls.append(args[0])

        class R:
            returncode = 0
        return R()

    monkeypatch.setattr("techforge_cli.commands.platform.subprocess.run", fake_run)
    result = CliRunner().invoke(dev_cmd)
    assert result.exit_code == 0
    assert calls and calls[0][-2:] == ["start", "--dev"]
