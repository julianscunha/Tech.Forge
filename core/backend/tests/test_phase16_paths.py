"""Fase 16 Slice 1 — Desktop paths oficiais por SO (spec §11/§12/§13).

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase16_paths.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from app.core import paths

pytestmark = pytest.mark.unit


def test_install_dir_is_the_repo_root_in_dev_tree():
    assert (paths.install_dir() / "core" / "backend").is_dir()


def test_install_dir_uses_executable_dir_when_frozen(monkeypatch, tmp_path):
    # PyInstaller: __file__ dentro do bundle não tem relação com a árvore
    # do repositório — descoberto rodando o .exe empacotado de verdade
    # (Slice 7), que falhava com "unable to open database file" porque
    # install_dir() calculava 5 parents de um __file__ congelado sem
    # sentido, achando um caminho que não existe.
    fake_exe = tmp_path / "techforge-backend.exe"
    fake_exe.touch()
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(fake_exe))

    assert paths.install_dir() == tmp_path


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


def test_ensure_user_data_dirs_creates_required_subdirectories(tmp_path):
    # Achado rodando o .exe empacotado de verdade (Slice 7): em produção
    # user_data_dir() aponta pra um diretório que ainda não existe no
    # primeiro start — sem isto, o SQLite falha com "unable to open
    # database file" (spec §14: "Create Data Directories").
    root = tmp_path / "does-not-exist-yet"
    paths.ensure_user_data_dirs(root)

    assert (root / "config").is_dir()
    assert (root / "logs").is_dir()
    assert (root / "modules" / "installed").is_dir()
    assert (root / "modules" / "repository").is_dir()
    assert (root / "modules" / "cache").is_dir()
