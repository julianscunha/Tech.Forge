"""Fase 16 Slice 5 — `techforge repair-check` (spec §33).

Run:  cd D:/Github/Tech.Forge && core/backend/.venv/Scripts/python.exe -m pytest cli/tests/test_phase16_repair_check.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "cli"))
sys.path.insert(0, str(ROOT / "core" / "backend"))

from techforge_cli.commands.repair import repair_check_cmd

pytestmark = pytest.mark.integration


@pytest.fixture()
def fake_install(tmp_path, monkeypatch):
    from app.module_trust import core_repair
    for rel_dir in core_repair.CORE_SOURCE_DIRS:
        d = tmp_path / rel_dir
        d.mkdir(parents=True)
        (d / "main.py").write_text("print('ok')\n", encoding="utf-8")
    monkeypatch.setattr(core_repair, "install_dir", lambda: tmp_path)
    return tmp_path


def test_no_manifest_reports_friendly_message_and_nonzero_exit(fake_install):
    result = CliRunner().invoke(repair_check_cmd)
    assert result.exit_code != 0
    assert "core-integrity.json" in result.output


def test_generate_flag_writes_manifest(fake_install):
    result = CliRunner().invoke(repair_check_cmd, ["--generate"])
    assert result.exit_code == 0
    assert (fake_install / "core-integrity.json").is_file()


def test_valid_installation_reports_ok(fake_install):
    CliRunner().invoke(repair_check_cmd, ["--generate"])
    result = CliRunner().invoke(repair_check_cmd)
    assert result.exit_code == 0
    assert "OK" in result.output or "VALID" in result.output


def test_tampered_installation_reports_modified_and_nonzero_exit(fake_install):
    from app.module_trust import core_repair
    CliRunner().invoke(repair_check_cmd, ["--generate"])
    tampered = fake_install / core_repair.CORE_SOURCE_DIRS[0] / "main.py"
    tampered.write_text("print('tampered')\n", encoding="utf-8")

    result = CliRunner().invoke(repair_check_cmd)
    assert result.exit_code != 0
    assert "main.py" in result.output
