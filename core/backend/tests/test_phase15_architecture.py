"""Fase 15 Slice 3 — architecture tests (spec §19/§20).

Protege decisões arquiteturais estruturais via `ast-grep` (ferramenta
mandatória do projeto para busca estrutural, CLAUDE.md) em vez de uma lib
Python nova tipo `import-linter`.

As regras de tipo de dependência (Application→Service permitido,
Service→Application bloqueado) já são testadas em
`test_phase8_1_dependency_governance.py` (Fase 8.1) — aqui cobrimos o que
ainda não tinha teste: módulo não importa interno do Core, módulo não
importa outro módulo diretamente.

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase15_architecture.py -q
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).parent.parent.parent.parent
MODULES_INSTALLED = REPO_ROOT / "modules" / "installed"

FORBIDDEN_CORE_IMPORT_PATTERNS = [
    "import app",
    "from app import $$$",
    "from app.$MOD import $$$",
]
FORBIDDEN_CROSS_MODULE_PATTERNS = [
    "from modules.installed.$OTHER import $$$",
    "import modules.installed.$OTHER",
]


def _ast_grep_path() -> str | None:
    return shutil.which("ast-grep")


def _ast_grep_available() -> bool:
    return _ast_grep_path() is not None


def _run_ast_grep(pattern: str, target: Path) -> list[dict]:
    exe = _ast_grep_path()
    args = [exe, "run", "-l", "python", "-p", pattern, "--json", str(target)]
    if exe.lower().endswith((".cmd", ".bat")):
        # Windows: arquivos .cmd/.bat exigem cmd.exe — CreateProcess não os invoca direto.
        args = ["cmd", "/c", *args]
    result = subprocess.run(args, capture_output=True, text=True, check=False)
    if not result.stdout.strip():
        return []
    return json.loads(result.stdout)


@pytest.mark.skipif(not _ast_grep_available(), reason="ast-grep não está no PATH")
@pytest.mark.parametrize("pattern", FORBIDDEN_CORE_IMPORT_PATTERNS)
def test_installed_modules_never_import_core_internals(pattern):
    """Módulo instalado não pode importar `app.*` (interno do Core) — deve usar o SDK."""
    matches = _run_ast_grep(pattern, MODULES_INSTALLED)
    offenders = [m["file"] for m in matches]
    assert not offenders, f"Import direto de Core internals em: {offenders} (padrão: {pattern})"


@pytest.mark.skipif(not _ast_grep_available(), reason="ast-grep não está no PATH")
@pytest.mark.parametrize("pattern", FORBIDDEN_CROSS_MODULE_PATTERNS)
def test_installed_modules_never_import_another_module_directly(pattern):
    """Módulo instalado não pode importar código de outro módulo diretamente."""
    matches = _run_ast_grep(pattern, MODULES_INSTALLED)
    offenders = [m["file"] for m in matches]
    assert not offenders, f"Import cross-module direto em: {offenders} (padrão: {pattern})"


def test_module_kv_storage_never_accepts_module_id_as_call_parameter():
    """Module Storage API: module_id é fixado na construção, nunca parâmetro de get/set/transaction
    (isolamento estrutural validado com api-and-interface-design na Fase 12 — este teste protege
    a decisão contra regressão futura)."""
    import inspect

    from app.services.module_storage import ModuleKVStorage

    for method_name in ("get", "set", "transaction"):
        method = getattr(ModuleKVStorage, method_name)
        params = list(inspect.signature(method).parameters)
        assert "module_id" not in params, f"{method_name} não pode aceitar module_id como parâmetro"
