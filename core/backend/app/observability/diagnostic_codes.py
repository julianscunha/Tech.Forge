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
    # Fase 16 §15/§35 — Launcher startup failures (não passam pelo Error
    # Registry: o backend nem chegou a responder, então usados diretamente
    # pelo launcher/__init__.py, não por ErrorRegistryService.
    "startup_backend": DiagnosticCode("TF-STARTUP-001", "Backend did not become ready in time"),
    "startup_frontend": DiagnosticCode("TF-STARTUP-002", "Frontend did not become ready in time"),
}


def resolve_diagnostic_code(source: str) -> Optional[DiagnosticCode]:
    """`source` é o mesmo valor já usado pelo Error Registry (execution |
    dependency | runtime) — não uma chave nova pra manter em sincronia."""
    return _CATALOG.get(source)
