"""Fase 15 Slice 2 — fixtures oficiais compartilhadas (spec §13).

Não retrofita os ~600 testes existentes (cada um já tem sua própria
construção de módulo/manifest, estável e testada) — serve os testes NOVOS
desta fase (architecture, contract, compatibility, release) e futuros, para
não repetir a mesma construção de diretório de módulo em cada arquivo novo.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import pytest
import yaml

BASE_MANIFEST: dict[str, Any] = {
    "id": "fixture_module",
    "name": "Fixture Module",
    "version": "1.0.0",
    "category": "Utilities",
    "vendor": "TechForge",
    "author": "TechForge",
    "description": "Módulo de fixture para testes.",
}


def make_manifest(**overrides: Any) -> dict[str, Any]:
    """Manifest válido mínimo, com overrides para casos inválidos/customizados."""
    manifest = dict(BASE_MANIFEST)
    manifest.update(overrides)
    return manifest


@pytest.fixture()
def module_dir_factory(tmp_path: Path) -> Callable[..., Path]:
    """Factory de diretório de módulo completo (estrutura + manifest.yaml).

    Uso: `module_dir_factory(module_id="x", manifest_overrides={...})`.
    """

    def _make(
        module_id: str = "fixture_module",
        manifest_overrides: dict[str, Any] | None = None,
        backend_code: str = "router = None\n",
        frontend_code: str = "",
        skip_manifest: bool = False,
    ) -> Path:
        mod_dir = tmp_path / "installed" / module_id
        for sub in ("backend", "frontend", "docs", "tests", "assets"):
            (mod_dir / sub).mkdir(parents=True, exist_ok=True)
        (mod_dir / "backend" / "api.py").write_text(backend_code, encoding="utf-8")
        (mod_dir / "frontend" / "main.js").write_text(frontend_code, encoding="utf-8")
        if not skip_manifest:
            manifest = make_manifest(id=module_id, **(manifest_overrides or {}))
            (mod_dir / "manifest.yaml").write_text(yaml.dump(manifest), encoding="utf-8")
        return mod_dir

    return _make


@pytest.fixture()
def valid_manifest() -> dict[str, Any]:
    return make_manifest()


@pytest.fixture(
    params=[
        pytest.param({"version": None}, id="missing_version"),
        pytest.param({"id": None}, id="missing_id"),
        pytest.param({"category": None}, id="missing_category"),
    ]
)
def invalid_manifest(request) -> dict[str, Any]:
    """Manifests inválidos por campo obrigatório ausente (spec §13: 'módulos inválidos')."""
    overrides = {k: v for k, v in request.param.items() if v is not None}
    manifest = make_manifest(**overrides)
    for key, value in request.param.items():
        if value is None:
            manifest.pop(key, None)
    return manifest
