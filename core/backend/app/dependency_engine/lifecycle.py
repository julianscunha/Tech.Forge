"""
Dependency Governance lifecycle hooks — Fase 8.1 §10/§11/§12/§13/§14
=========================================================================
Consultados por activate/deactivate/remove antes de mutar o estado do
módulo (§28/§29). Não persiste nada — apenas responde "pode?" com base no
DependencyResolver (Slice 4).
"""
from __future__ import annotations

from app.dependency_engine.models import Dependency, DependencyStatus, TargetType
from app.dependency_engine.parser import DependencyParseError, DependencyParser
from app.dependency_engine.resolver import DependencyResolver
from app.module_engine.enums import ModuleStatus


def check_can_activate(module_id: str, module_registry,
                        service_registry) -> tuple[bool, list[Dependency]]:
    """
    §10/§14 — bloqueia ativação se alguma dependência obrigatória não está
    SATISFIED. OPTIONAL_UNAVAILABLE nunca bloqueia (é sempre de dependência
    opcional, por definição do Resolver).
    """
    deps = DependencyResolver.resolve(module_id, module_registry, service_registry)
    blocking = [d for d in deps if d.required and d.status != DependencyStatus.SATISFIED]
    return (not blocking, blocking)


def _dependents_of(module_id: str, module_registry, service_registry) -> list[str]:
    dependents: list[str] = []
    for entry in module_registry.all():
        if entry.module_id == module_id or entry.status != ModuleStatus.INSTALLED:
            continue
        raw = entry.manifest_raw.get("dependencies") or []
        try:
            deps = DependencyParser.parse(raw)
        except DependencyParseError:
            continue

        for dep in deps:
            if not dep.required:
                continue
            if dep.target_type == TargetType.MODULE and dep.target_id == module_id:
                dependents.append(entry.module_id)
                break
            if dep.target_type == TargetType.CAPABILITY:
                providers = service_registry.find_capability(dep.target_id)
                if any(p.module_id == module_id for p in providers):
                    dependents.append(entry.module_id)
                    break

    return dependents


def check_can_deactivate(module_id: str, module_registry,
                          service_registry) -> tuple[bool, list[str]]:
    """§11/§12 — bloqueia se existe dependent INSTALLED com dependência obrigatória."""
    dependents = _dependents_of(module_id, module_registry, service_registry)
    return (not dependents, dependents)


def check_can_remove(module_id: str, module_registry,
                      service_registry) -> tuple[bool, list[str]]:
    """§13 — mesma regra do deactivate."""
    return check_can_deactivate(module_id, module_registry, service_registry)
