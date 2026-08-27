"""
DependencyResolver — Fase 8.1 §7/§8/§15/§23
================================================
Combina DependencyGraph + ModuleRegistry + ServiceRegistry pra preencher o
`status` de cada Dependency declarada por um módulo (os 7 estados de
DependencyStatus). Conflito de capability reaproveita
`ServiceRegistry.list_conflicts()` (Fase 8) — não duplica a discovery.
"""
from __future__ import annotations

from app.dependency_engine.graph import DependencyGraph
from app.dependency_engine.models import Dependency, DependencyStatus, TargetType
from app.dependency_engine.parser import DependencyParseError, DependencyParser
from app.module_engine.enums import ModuleStatus
from app.service_registry.descriptor import ServiceStatus


class DependencyResolver:

    @staticmethod
    def resolve(module_id: str, module_registry, service_registry) -> list[Dependency]:
        entry = module_registry.get(module_id)
        if entry is None:
            return []

        raw = entry.manifest_raw.get("dependencies") or []
        try:
            deps = DependencyParser.parse(raw)
        except DependencyParseError:
            return []

        cyclic_modules: set[str] = set()
        for cycle in DependencyGraph.build(module_registry, service_registry).detect_cycles():
            cyclic_modules.update(cycle)
        conflicts = service_registry.list_conflicts()

        for dep in deps:
            if dep.target_type == TargetType.MODULE:
                dep.status = _resolve_module(dep, module_id, cyclic_modules, module_registry)
            else:
                dep.status = _resolve_capability(dep, conflicts, service_registry)

        return deps


def _resolve_module(dep: Dependency, module_id: str, cyclic_modules: set[str],
                     module_registry) -> DependencyStatus:
    if module_id in cyclic_modules and dep.target_id in cyclic_modules:
        return DependencyStatus.CYCLIC

    target = module_registry.get(dep.target_id)
    if target is None:
        return DependencyStatus.MISSING if dep.required else DependencyStatus.OPTIONAL_UNAVAILABLE

    if target.status == ModuleStatus.DISABLED:
        return DependencyStatus.DISABLED if dep.required else DependencyStatus.OPTIONAL_UNAVAILABLE

    if target.status != ModuleStatus.INSTALLED:
        return DependencyStatus.MISSING if dep.required else DependencyStatus.OPTIONAL_UNAVAILABLE

    if not dep.satisfies_version(target.version):
        return DependencyStatus.INCOMPATIBLE_VERSION

    return DependencyStatus.SATISFIED


def _resolve_capability(dep: Dependency, conflicts: dict, service_registry) -> DependencyStatus:
    providers = service_registry.find_capability(dep.target_id)
    if not providers:
        return DependencyStatus.MISSING if dep.required else DependencyStatus.OPTIONAL_UNAVAILABLE

    active = [p for p in providers if p.status == ServiceStatus.ACTIVE]
    if not active:
        return DependencyStatus.DISABLED if dep.required else DependencyStatus.OPTIONAL_UNAVAILABLE

    if dep.target_id in conflicts:
        return DependencyStatus.CONFLICT

    if not dep.satisfies_version(active[0].service_version):
        return DependencyStatus.INCOMPATIBLE_VERSION

    return DependencyStatus.SATISFIED
