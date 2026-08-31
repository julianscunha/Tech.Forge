"""Fase 16 Slice 1 — Desktop paths oficiais por SO (spec §11/§12/§13).

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase16_paths.py -q
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.core import paths

pytestmark = pytest.mark.unit


def test_install_dir_is_the_repo_root_in_dev_tree():
    assert (paths.install_dir() / "core" / "backend").is_dir()


def test_user_data_dir_matches_install_dir_inside_dev_tree(monkeypatch):
    monkeypatch.delenv("TECHFORGE_DATA_DIR", raising=False)
    assert paths.user_data_dir() == paths.install_dir()


def test_user_data_dir_uses_platformdirs_outside_dev_tree(monkeypatch, tmp_path):
    monkeypatch.delenv("TECHFORGE_DATA_DIR", raising=False)
    monkeypatch.setattr(paths, "install_dir", lambda: tmp_path)

    import platformdirs

    expected = Path(platformdirs.user_data_dir("TechForge", "TechForge"))
    assert paths.user_data_dir() == expected


def test_user_data_dir_env_override_wins_even_outside_dev_tree(monkeypatch, tmp_path):
    override = tmp_path / "custom-data"
    monkeypatch.setenv("TECHFORGE_DATA_DIR", str(override))
    monkeypatch.setattr(paths, "install_dir", lambda: tmp_path)

    assert paths.user_data_dir() == override


def test_user_data_dir_env_override_wins_inside_dev_tree(monkeypatch, tmp_path):
    override = tmp_path / "custom-data"
    monkeypatch.setenv("TECHFORGE_DATA_DIR", str(override))

    assert paths.user_data_dir() == override
