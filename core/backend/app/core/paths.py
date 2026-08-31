"""Desktop paths oficiais por SO (Fase 16 §11/§12/§13).

Separa Application Install (código, read-only em produção) de User Data
(banco, logs, módulos instalados) — pré-requisito de instalador/update/
uninstall. Em árvore de desenvolvimento (com `.git`), ambos coincidem com a
raiz do repositório, preservando o comportamento atual de dev/CI.
"""
from __future__ import annotations

import os
from pathlib import Path

import platformdirs

APP_NAME = "TechForge"
APP_AUTHOR = "TechForge"


def install_dir() -> Path:
    """Raiz do código instalado — hoje sempre a raiz do repositório."""
    return Path(__file__).resolve().parent.parent.parent.parent.parent


def _is_dev_tree(root: Path) -> bool:
    return (root / ".git").exists()


def user_data_dir() -> Path:
    """Onde ficam dados do usuário (DB, logs, módulos, cache).

    Ordem de resolução: `TECHFORGE_DATA_DIR` (override explícito) > árvore
    de desenvolvimento (mesmo diretório do código) > diretório de dados do
    SO via `platformdirs` (produção/instalado).
    """
    if override := os.environ.get("TECHFORGE_DATA_DIR"):
        return Path(override)

    root = install_dir()
    if _is_dev_tree(root):
        return root

    return Path(platformdirs.user_data_dir(APP_NAME, APP_AUTHOR))
