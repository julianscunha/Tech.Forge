"""
Dependency Governance — Fase 8.1
===================================
Governa relações declaradas entre módulos: resolução, validação de
compatibilidade, detecção de conflitos e ciclos, respeitando a regra
arquitetural Service Module ✗→ Application Module.
"""
from app.dependency_engine.models import Dependency, DependencyStatus, TargetType
from app.dependency_engine.parser import DependencyParser, DependencyParseError
from app.dependency_engine.validator import DependencyCheck, DependencyValidator
from app.dependency_engine.graph import DependencyGraph, Edge

__all__ = [
    "Dependency", "DependencyStatus", "TargetType",
    "DependencyParser", "DependencyParseError",
    "DependencyCheck", "DependencyValidator",
    "DependencyGraph", "Edge",
]
