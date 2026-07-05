"""
Documentation Completeness Checker — §16 Documentation First Principle
=========================================================================
Implements the "Definition of Done" rule: a module is not considered
complete without Implementation + Contract + Documentation + Example.

This is read-only analysis — it does not block installation (that remains
the Package Manager's job via compatibility checks). It surfaces gaps so
developers and the Marketplace governance rule can enforce them.

Definition of Done (per §16):
  1. Implementation — backend/main.py and frontend/index.tsx exist
  2. Contract        — docs/contracts/api.yaml exists and is well-formed
                        (only required for module_type: service)
  3. Documentation    — docs/overview.md exists and is non-trivial
  4. Example          — at least one functional example exists
                        (docs/examples/basic.md at minimum)

Service modules additionally require all three example tiers:
  docs/examples/basic.md
  docs/examples/advanced.md
  docs/examples/integration.md
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from app.doc_engine.api_yaml_parser import APIYamlParser
from app.doc_engine.models import ServiceContract, ServiceExport


# ── Result model ──────────────────────────────────────────────────────────────

@dataclass
class DoDCheck:
    """One Definition-of-Done criterion."""
    name:     str
    passed:   bool
    required: bool        # False = recommended but not mandatory
    detail:   str


@dataclass
class CompletenessReport:
    """
    Full Definition-of-Done report for a single module.

    is_complete is True only when every `required=True` check passes.
    Service modules have stricter requirements (full contract + 3 example tiers).
    """
    module_id:    str
    module_type:  str                  # "application" | "service"
    checks:       list[DoDCheck] = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        return all(c.passed for c in self.checks if c.required)

    @property
    def score(self) -> float:
        """Percentage of required checks passing, 0.0–100.0."""
        required = [c for c in self.checks if c.required]
        if not required:
            return 100.0
        passed = sum(1 for c in required if c.passed)
        return round(100.0 * passed / len(required), 1)

    @property
    def missing(self) -> list[str]:
        return [c.name for c in self.checks if c.required and not c.passed]


# ── Contract validation (§16 — exports must declare name, description,
#    parameters, types, required flag, returns, examples) ───────────────────

def validate_contract_completeness(contract: Optional[ServiceContract]) -> list[DoDCheck]:
    """
    Validate that a ServiceContract meets §16 requirements for every export:
    name, description, parameters (with type + required), returns, examples.
    """
    checks: list[DoDCheck] = []

    if contract is None:
        checks.append(DoDCheck(
            name="Contract present", passed=False, required=True,
            detail="No docs/contracts/api.yaml found.",
        ))
        return checks

    checks.append(DoDCheck(
        name="Contract present", passed=True, required=True,
        detail=f"service_id={contract.service_id}",
    ))

    if not contract.exports:
        checks.append(DoDCheck(
            name="Contract has exports", passed=False, required=True,
            detail="api.yaml has no entries under 'exports'.",
        ))
        return checks

    checks.append(DoDCheck(
        name="Contract has exports", passed=True, required=True,
        detail=f"{len(contract.exports)} export(s) declared",
    ))

    for exp in contract.exports:
        checks.extend(_validate_export(exp))

    return checks


def _validate_export(exp: ServiceExport) -> list[DoDCheck]:
    prefix = f"export '{exp.name or '?'}'"
    out: list[DoDCheck] = []

    out.append(DoDCheck(
        name=f"{prefix}: has name", passed=bool(exp.name), required=True,
        detail=exp.name or "missing name",
    ))
    out.append(DoDCheck(
        name=f"{prefix}: has description", passed=bool(exp.description), required=True,
        detail=exp.description or "missing description",
    ))

    # Each parameter must declare type and required flag explicitly
    params_ok = True
    for p in exp.parameters:
        if not p.get("type") or "required" not in p:
            params_ok = False
    out.append(DoDCheck(
        name=f"{prefix}: parameters typed", passed=params_ok, required=True,
        detail=(f"{len(exp.parameters)} parameter(s), all typed"
                if params_ok else "one or more parameters missing type/required"),
    ))

    out.append(DoDCheck(
        name=f"{prefix}: has returns", passed=bool(exp.returns), required=True,
        detail=exp.returns or "missing returns",
    ))
    out.append(DoDCheck(
        name=f"{prefix}: has examples", passed=bool(exp.examples), required=True,
        detail=f"{len(exp.examples)} example(s)" if exp.examples else "no examples provided",
    ))

    return out


# ── Module-level completeness ─────────────────────────────────────────────────

class DocCompletenessChecker:
    """
    Computes a full §16 Definition-of-Done report for one module directory.

    Usage:
        report = DocCompletenessChecker.check(
            module_path=Path("modules/installed/my_module"),
            module_type="service",
        )
    """

    EXAMPLE_TIERS = ("basic.md", "advanced.md", "integration.md")

    @classmethod
    def check(cls, module_path: Path, module_type: str = "application") -> CompletenessReport:
        module_id = module_path.name
        report = CompletenessReport(module_id=module_id, module_type=module_type)

        # ── 1. Implementation ─────────────────────────────────────────────────
        backend_ok  = (module_path / "backend" / "main.py").exists()
        frontend_ok = (module_path / "frontend" / "index.tsx").exists()
        report.checks.append(DoDCheck(
            "Implementation: backend", backend_ok, True,
            "backend/main.py present" if backend_ok else "backend/main.py missing",
        ))
        report.checks.append(DoDCheck(
            "Implementation: frontend", frontend_ok, True,
            "frontend/index.tsx present" if frontend_ok else "frontend/index.tsx missing",
        ))

        # ── 2. Documentation ──────────────────────────────────────────────────
        docs_dir = module_path / "docs"
        overview = docs_dir / "overview.md"
        overview_ok = overview.exists() and len(overview.read_text(encoding="utf-8").strip()) > 40
        report.checks.append(DoDCheck(
            "Documentation: overview.md", overview_ok, True,
            "docs/overview.md present and non-trivial" if overview_ok
            else "docs/overview.md missing or too short (<40 chars)",
        ))

        # ── 3. Contract — required for service modules, recommended otherwise ─
        contract_path = docs_dir / "contracts" / "api.yaml"
        contract = APIYamlParser.parse(contract_path, module_id)
        is_service = module_type == "service"

        if is_service:
            report.checks.extend(validate_contract_completeness(contract))
        else:
            # Application modules: contract recommended but not mandatory
            report.checks.append(DoDCheck(
                "Contract present (recommended)", contract is not None, False,
                "docs/contracts/api.yaml present" if contract
                else "no contract published (optional for application modules)",
            ))

        # ── 4. Examples ────────────────────────────────────────────────────────
        examples_dir = docs_dir / "examples"
        basic_exists = (examples_dir / "basic.md").exists()

        report.checks.append(DoDCheck(
            "Example: basic.md", basic_exists, True,
            "docs/examples/basic.md present" if basic_exists
            else "docs/examples/basic.md missing — at least one example is required",
        ))

        # Service modules require all three tiers
        for tier in ("advanced.md", "integration.md"):
            exists = (examples_dir / tier).exists()
            report.checks.append(DoDCheck(
                f"Example: {tier}", exists, is_service,
                f"docs/examples/{tier} present" if exists
                else f"docs/examples/{tier} missing"
                     + (" — required for service modules" if is_service else " (recommended)"),
            ))

        return report
