"""Diagnostic Codes — Fase 14 §20.

Catálogo inicial mapeando as origens de erro já capturadas pelo Error
Registry (slice 10) para códigos estáveis. Deliberadamente pequeno: só
os enums/origens que já existem de verdade no código, não uma lista
extensa especulativa (spec pede documentação por código — melhor
começar com poucos reais do que muitos inventados).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class DiagnosticCode:
    code: str
    title: str


_CATALOG: dict[str, DiagnosticCode] = {
    "execution": DiagnosticCode("TF-EXECUTION-001", "Module execution failed"),
    "dependency": DiagnosticCode("TF-DEPENDENCY-001", "Invalid module dependency declared"),
    "runtime": DiagnosticCode("TF-RUNTIME-001", "Runtime component stopped responding"),
}


def resolve_diagnostic_code(source: str) -> Optional[DiagnosticCode]:
    """`source` é o mesmo valor já usado pelo Error Registry (execution |
    dependency | runtime) — não uma chave nova pra manter em sincronia."""
    return _CATALOG.get(source)
