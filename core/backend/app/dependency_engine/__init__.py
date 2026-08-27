"""
Dependency Governance — Fase 8.1
===================================
Governa relações declaradas entre módulos: resolução, validação de
compatibilidade, detecção de conflitos e ciclos, respeitando a regra
arquitetural Service Module ✗→ Application Module.
"""
from app.dependency_engine.models import Dependency, DependencyStatus, TargetType
from app.dependency_engine.parser import DependencyParser, DependencyParseError

__all__ = [
    "Dependency", "DependencyStatus", "TargetType",
    "DependencyParser", "DependencyParseError",
]
