"""Fase 16 Slice 5 — `techforge repair-check` (spec §33).

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase16_repair_check.py -q
"""
from __future__ import annotations

import pytest

from app.module_trust import core_repair
from app.module_trust.integrity import IntegrityStatus

pytestmark = pytest.mark.unit


@pytest.fixture()
def fake_install(tmp_path, monkeypatch):
    for rel_dir in core_repair.CORE_SOURCE_DIRS:
        d = tmp_path / rel_dir
        d.mkdir(parents=True)
        (d / "main.py").write_text("print('ok')\n", encoding="utf-8")
    monkeypatch.setattr(core_repair, "install_dir", lambda: tmp_path)
    return tmp_path


def test_verify_without_manifest_reports_invalid(fake_install):
    result = core_repair.verify_core_integrity()
    assert result.status == IntegrityStatus.INVALID_MANIFEST


def test_generate_then_verify_reports_valid(fake_install):
    core_repair.write_core_manifest()
    result = core_repair.verify_core_integrity()
    assert result.status == IntegrityStatus.VALID


def test_tampered_file_is_detected(fake_install):
    core_repair.write_core_manifest()

    tampered = fake_install / core_repair.CORE_SOURCE_DIRS[0] / "main.py"
    tampered.write_text("print('tampered')\n", encoding="utf-8")

    result = core_repair.verify_core_integrity()
    assert result.status == IntegrityStatus.MODIFIED
    assert any("main.py" in path for path in result.modified_files)


def test_missing_file_is_detected(fake_install):
    core_repair.write_core_manifest()

    (fake_install / core_repair.CORE_SOURCE_DIRS[0] / "main.py").unlink()

    result = core_repair.verify_core_integrity()
    assert result.status == IntegrityStatus.MISSING_FILE
