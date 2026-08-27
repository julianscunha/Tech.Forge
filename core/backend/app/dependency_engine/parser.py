"""
DependencyParser — Fase 8.1 §16
==================================
Lê o campo `dependencies` já presente em `ParsedManifest.dependencies`
(passado adiante cru pelo ManifestParser) e produz modelos tipados.
"""
from __future__ import annotations

from packaging.specifiers import InvalidSpecifier, SpecifierSet

from app.dependency_engine.models import Dependency, TargetType


class DependencyParseError(Exception):
    """Raised when a declared dependency is structurally invalid."""


class DependencyParser:

    @staticmethod
    def parse(raw: list[dict]) -> list[Dependency]:
        deps: list[Dependency] = []
        for item in raw:
            target = item.get("target") or {}
            raw_type = target.get("type")
            target_id = str(target.get("id", "")).strip()

            try:
                target_type = TargetType(raw_type)
            except ValueError:
                raise DependencyParseError(
                    f"Invalid dependency target type: {raw_type!r} "
                    f"(expected 'module' or 'capability')"
                )

            if not target_id:
                raise DependencyParseError("Dependency target id must not be empty")

            version_range = item.get("version_range") or None
            if version_range:
                try:
                    SpecifierSet(version_range)
                except InvalidSpecifier as exc:
                    raise DependencyParseError(
                        f"Invalid version_range {version_range!r}: {exc}"
                    ) from exc

            deps.append(Dependency(
                target_type=target_type,
                target_id=target_id,
                version_range=version_range,
                required=bool(item.get("required", True)),
            ))
        return deps
