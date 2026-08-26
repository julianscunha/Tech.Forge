"""Fase 7 §12 — validate-module inclui seção Documentation Compliance.

Run:  cd D:/Github/Tech.Forge && core/backend/.venv/Scripts/python.exe -m pytest cli/tests/test_phase7_compliance_cli.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "cli"))
sys.path.insert(0, str(ROOT / "core" / "backend"))

from techforge_cli.commands.validate_module import validate_module_cmd


def _make_module(tmp_path: Path, with_docs: bool = True) -> Path:
    mod = tmp_path / "my_mod"
    (mod / "backend").mkdir(parents=True)
    manifest = (
        "id: my_mod\nname: My Mod\nversion: 1.0.0\n"
        "icon: box\norder: 1\nentry_backend: backend/main.py\n"
    )
    (mod / "manifest.yaml").write_text(manifest, encoding="utf-8")
    (mod / "backend" / "main.py").write_text(
        "router = None\n", encoding="utf-8")
    if with_docs:
        docs = mod / "docs"
        docs.mkdir()
        (docs / "overview.md").write_text(
            "# My Mod\n\nOverview content here.\n\n## Example\n\n```\nrun()\n```\n",
            encoding="utf-8")
    return mod


def test_compliance_section_appears_in_output(tmp_path):
    """Saída da CLI inclui a seção 'Documentation Compliance' (§12)."""
    result = CliRunner().invoke(validate_module_cmd, [str(_make_module(tmp_path))])
    assert "Documentation Compliance" in result.output


def test_compliance_complete_result(tmp_path):
    """Módulo com overview + exemplo → Result: COMPLETE."""
    result = CliRunner().invoke(validate_module_cmd, [str(_make_module(tmp_path))])
    assert "COMPLETE" in result.output


def test_compliance_missing_docs_shows_failures(tmp_path):
    """Sem docs → seção presente com falhas, não crasha."""
    result = CliRunner().invoke(validate_module_cmd, [str(_make_module(tmp_path, with_docs=False))])
    assert "Documentation Compliance" in result.output
    assert "FAIL" in result.output or "WARN" in result.output
