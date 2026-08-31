"""Desktop paths oficiais por SO (Fase 16 §11/§12/§13).

Separa Application Install (código, read-only em produção) de User Data
(banco, logs, módulos instalados) — pré-requisito de instalador/update/
uninstall. Em árvore de desenvolvimento (com `.git`), ambos coincidem com a
raiz do repositório, preservando o comportamento atual de dev/CI.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import platformdirs

APP_NAME = "TechForge"
APP_AUTHOR = "TechForge"


def install_dir() -> Path:
    """Raiz do código instalado.

    Em árvore de dev/CI, a raiz do repositório (5 níveis acima deste
    arquivo). Dentro de um executável PyInstaller (`sys.frozen`), esse
    `__file__` não tem relação com a árvore real — install_dir vira o
    diretório do próprio .exe (achado rodando o build empacotado de
    verdade, Fase 16 §10: sem isto, `user_data_dir()` calculava um
    caminho inexistente e o SQLite falhava com "unable to open database
    file" no primeiro start empacotado).
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
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


def ensure_user_data_dirs(root: Path) -> None:
    """Primeiro startup (spec §14: "Create Data Directories"). Em árvore de
    dev esses diretórios já existem (checados no repo) — no-op silencioso;
    em produção instalada, `platformdirs.user_data_dir()` pode apontar pra
    um caminho que ainda não existe, e o SQLite não cria diretórios
    sozinho ao abrir o arquivo do banco."""
    for sub in ("config", "logs", "modules/installed", "modules/repository", "modules/cache"):
        (root / sub).mkdir(parents=True, exist_ok=True)
