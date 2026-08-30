"""Fase 15 Slice 1 — todo arquivo de teste declara um marker de nível.

Spec §4: "Não colocar todos os testes em uma única categoria." Este guard
impede que um arquivo novo entre no repo sem `pytestmark` — falha primeiro
(RED) até que os arquivos existentes sejam marcados (GREEN).

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase15_test_markers.py -q
"""
from __future__ import annotations

import re
from pathlib import Path

ALLOWED_MARKERS = {"unit", "integration", "contract", "e2e", "regression", "smoke"}
TESTS_DIR = Path(__file__).parent
EXCLUDED = {"__init__.py", "test_phase15_test_markers.py"}

_PYTESTMARK_RE = re.compile(r"pytestmark\s*=\s*pytest\.mark\.(\w+)")


def _test_files():
    return sorted(p for p in TESTS_DIR.glob("test_*.py") if p.name not in EXCLUDED)


def test_every_test_file_declares_a_level_marker():
    missing = []
    unknown = []
    for path in _test_files():
        text = path.read_text(encoding="utf-8")
        match = _PYTESTMARK_RE.search(text)
        if not match:
            missing.append(path.name)
        elif match.group(1) not in ALLOWED_MARKERS:
            unknown.append((path.name, match.group(1)))
    assert not missing, f"Arquivos sem pytestmark de nível: {missing}"
    assert not unknown, f"Marker desconhecido: {unknown}"


def test_at_least_one_file_exists_to_check():
    assert len(_test_files()) > 10
