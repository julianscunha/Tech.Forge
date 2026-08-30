"""
DependencyValidator — Fase 8.1 §3/§17
========================================
Verifica: estrutura, tipo válido, id válido, versão válida (via
DependencyParser), duplicidade, e a regra arquitetural obrigatória
(Service Module ✗→ Application Module).
"""
from __future__ import annotations

from dataclasses import dataclass

from app.dependency_engine.models import TargetType
from app.dependency_engine.parser import DependencyParseError, DependencyParser
from app.observability.metrics import metric_emitter


@dataclass
class DependencyCheck:
    name:     str
    passed:   bool
    required: bool
    detail:   str


class DependencyValidator:

    @staticmethod
    def validate(module_type: str, raw_dependencies: list[dict],
                 module_registry=None) -> list[DependencyCheck]:
        """Returns one or more DependencyCheck per declared dependency."""
        checks: list[DependencyCheck] = []
        seen: set[tuple[str, str]] = set()

        for item in raw_dependencies:
            target = item.get("target") or {}
            target_id = str(target.get("id", "?"))
            target_type_raw = str(target.get("type", "?"))
            label = f"{target_type_raw}:{target_id}"

            try:
                dep = DependencyParser.parse([item])[0]
            except DependencyParseError as exc:
                checks.append(DependencyCheck(
                    f"Dependency structure: {label}", False, True, str(exc),
                ))
                continue

            checks.append(DependencyCheck(
                f"Dependency structure: {label}", True, True, "valid",
            ))

            key = (dep.target_type.value, dep.target_id)
            if key in seen:
                checks.append(DependencyCheck(
                    f"Duplicate dependency: {label}", False, True,
                    f"{label} is declared more than once",
                ))
            seen.add(key)

            if dep.target_type == TargetType.MODULE:
                checks.append(_check_direction(module_type, dep.target_id, module_registry))

        failed_required = sum(1 for c in checks if not c.passed and c.required)
        if failed_required:
            metric_emitter.counter("dependency_failures").inc(failed_required)

        return checks


def _check_direction(module_type: str, target_id: str, module_registry) -> DependencyCheck:
    """
    §3 — Service Module cannot depend on an Application Module. Only
    checkable when the target module is known (already installed); an
    unknown target neither passes nor fails — it is simply not reported.
    """
    if module_type != "service" or module_registry is None:
        return DependencyCheck(
            f"Dependency direction: {target_id}", True, False, "not applicable",
        )

    target_entry = module_registry.get(target_id)
    if target_entry is None:
        return DependencyCheck(
            f"Dependency direction: {target_id}", True, False,
            "target not installed — direction cannot be validated yet",
        )

    target_module_type = getattr(target_entry, "module_type", "application")
    if target_module_type == "application":
        return DependencyCheck(
            f"Dependency direction: {target_id}", False, True,
            f"INVALID_DEPENDENCY_DIRECTION — a service module cannot depend "
            f"on application module '{target_id}'",
        )
    return DependencyCheck(
        f"Dependency direction: {target_id}", True, True,
        f"'{target_id}' is a service module — direction OK",
    )
