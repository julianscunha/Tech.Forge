"""Fase 12 Slice 6 — Filesystem paths oficiais (spec §20/§21).

`ModulePaths` substitui o `Path` solto em `ModuleExecutionContext.paths`;
criados fisicamente na instalação; excluídos do hash de integridade
(Fase 10) por serem dados de runtime, não código do módulo.

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase12_module_paths.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))
sys.path.insert(0, str(Path(__file__).parent))

from app.module_runtime.paths import ModulePaths

import asyncio

from test_phase4 import MANIFEST_BASE, make_mod_file, make_package_manager


def test_for_module_derives_all_four_official_subpaths(tmp_path):
    root = tmp_path / "my_module"
    paths = ModulePaths.for_module(root)
    assert paths.root == root
    assert paths.data == root / "data"
    assert paths.cache == root / "cache"
    assert paths.exports == root / "exports"
    assert paths.temp == root / "temp"


def test_ensure_exist_creates_all_four_directories(tmp_path):
    root = tmp_path / "my_module"
    root.mkdir()
    paths = ModulePaths.for_module(root)
    paths.ensure_exist()
    assert paths.data.is_dir()
    assert paths.cache.is_dir()
    assert paths.exports.is_dir()
    assert paths.temp.is_dir()


def test_ensure_exist_is_idempotent(tmp_path):
    root = tmp_path / "my_module"
    root.mkdir()
    paths = ModulePaths.for_module(root)
    paths.ensure_exist()
    paths.ensure_exist()  # não deve levantar
    assert paths.data.is_dir()


def test_module_execution_context_build_exposes_module_paths():
    from fastapi.testclient import TestClient

    from app.main import app
    from app.module_runtime.context import ModuleExecutionContext
    from app.module_engine.registry import registry as module_registry

    with TestClient(app):
        ctx = ModuleExecutionContext.build("hello_world", module_registry)

    assert ctx is not None
    assert ctx.paths.root.name == "hello_world"
    assert ctx.paths.data == ctx.paths.root / "data"
    assert ctx.paths.cache == ctx.paths.root / "cache"
    assert ctx.paths.exports == ctx.paths.root / "exports"
    assert ctx.paths.temp == ctx.paths.root / "temp"


def test_integrity_manifest_excludes_cache_exports_temp(tmp_path):
    from app.module_trust.integrity import IntegrityStatus, write_integrity_manifest, verify_integrity

    mod_dir = tmp_path / "int_paths_test"
    (mod_dir / "backend").mkdir(parents=True)
    (mod_dir / "backend" / "main.py").write_text("x=1\n", encoding="utf-8")
    (mod_dir / "cache").mkdir()
    (mod_dir / "exports").mkdir()
    (mod_dir / "temp").mkdir()
    (mod_dir / "cache" / "c.tmp").write_text("cache", encoding="utf-8")
    (mod_dir / "exports" / "r.csv").write_text("export", encoding="utf-8")
    (mod_dir / "temp" / "t.tmp").write_text("temp", encoding="utf-8")

    write_integrity_manifest(mod_dir)

    # Escreve novos arquivos nessas pastas depois do manifesto — não deve
    # contar como modificação (não são código do módulo).
    (mod_dir / "cache" / "new.tmp").write_text("novo", encoding="utf-8")
    (mod_dir / "exports" / "new.csv").write_text("novo", encoding="utf-8")
    (mod_dir / "temp" / "new.tmp").write_text("novo", encoding="utf-8")

    result = verify_integrity(mod_dir)
    assert result.status == IntegrityStatus.VALID


def test_install_creates_official_runtime_directories(tmp_path):
    pm = make_package_manager(tmp_path)
    mod = make_mod_file(tmp_path, MANIFEST_BASE.copy())
    result = asyncio.run(pm.install(mod))
    assert result.success, result.message

    installed = tmp_path / "installed" / "test_pkg"
    assert (installed / "data").is_dir()
    assert (installed / "cache").is_dir()
    assert (installed / "exports").is_dir()
    assert (installed / "temp").is_dir()
