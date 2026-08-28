"""
/api/v1/modules/{id}/dependencies|dependents, /api/v1/dependencies/* —
Dependency Governance (Fase 8.1 §25/§26)
=============================================
Somente consulta — reusa DependencyResolver/DependencyValidator/
DependencyGraph (Slices 2-4), nenhuma lógica de discovery duplicada.
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.dependency_engine.graph import DependencyGraph
from app.dependency_engine.lifecycle import check_can_deactivate
from app.dependency_engine.resolver import DependencyResolver
from app.dependency_engine.validator import DependencyValidator
from app.module_engine.registry import registry
from app.service_registry.registry import service_registry

modules_router = APIRouter(prefix="/modules", tags=["dependency-governance"])
dependencies_router = APIRouter(prefix="/dependencies", tags=["dependency-governance"])


class DependencyRead(BaseModel):
    target_type:   str
    target_id:     str
    version_range: str | None
    required:      bool
    status:        str | None


class DependencyCheckRead(BaseModel):
    name:     str
    passed:   bool
    required: bool
    detail:   str


def _to_read(dep) -> DependencyRead:
    return DependencyRead(
        target_type=dep.target_type.value, target_id=dep.target_id,
        version_range=dep.version_range, required=dep.required,
        status=dep.status.value if dep.status else None,
    )


@modules_router.get("/{module_id}/dependencies", response_model=list[DependencyRead],
                    summary="Resolved dependencies of a module (§7/§8)")
async def get_dependencies(module_id: str) -> list[DependencyRead]:
    deps = DependencyResolver.resolve(module_id, registry, service_registry)
    return [_to_read(d) for d in deps]


@modules_router.get("/{module_id}/dependents", response_model=list[str],
                    summary="Installed modules that depend on this one (§11/§12)")
async def get_dependents(module_id: str) -> list[str]:
    _, dependents = check_can_deactivate(module_id, registry, service_registry)
    return dependents


@dependencies_router.get("/validate", response_model=dict[str, list[DependencyCheckRead]],
                         summary="Validate declared dependencies of every installed module (§17)")
async def validate_all() -> dict[str, list[DependencyCheckRead]]:
    report: dict[str, list[DependencyCheckRead]] = {}
    for entry in registry.all():
        raw = entry.manifest_raw.get("dependencies") or []
        if not raw:
            continue
        checks = DependencyValidator.validate(entry.module_type, raw, module_registry=registry)
        report[entry.module_id] = [DependencyCheckRead(**vars(c)) for c in checks]
    return report


@dependencies_router.get("/graph", response_model=dict[str, str],
                         summary="Dependency graph as Mermaid flowchart (§6/§22)")
async def get_graph() -> dict[str, str]:
    graph = DependencyGraph.build(registry, service_registry)
    return {"mermaid": graph.export_mermaid()}
