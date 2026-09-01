"""
TechForge CLI — Module Validator
==================================
Standalone validation logic used by both `techforge validate-module` and
the automated test suite.

Checks:
  1. Directory existence
  2. manifest.yaml parseable and all required fields present
  3. Required subdirectory structure
  4. Entry point files exist on disk
  5. Platform compatibility window is valid semver
  6. Backend exports router and module (contract check)
  7. Frontend exports moduleConfig (contract check)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# ── Result ────────────────────────────────────────────────────────────────────

@dataclass
class CheckResult:
    name:    str
    passed:  bool
    message: str
    level:   str = "error"   # "error" | "warning"


@dataclass
class ValidationReport:
    module_path: Path
    checks:      list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks if c.level == "error")

    @property
    def error_count(self) -> int:
        return sum(1 for c in self.checks if not c.passed and c.level == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for c in self.checks if not c.passed and c.level == "warning")

    def add(self, name: str, passed: bool, message: str, level: str = "error") -> None:
        self.checks.append(CheckResult(name=name, passed=passed, message=message, level=level))


# ── Validator ─────────────────────────────────────────────────────────────────

REQUIRED_MANIFEST_FIELDS = (
    "id", "name", "version", "category", "vendor",
    "author", "description", "entry_backend", "entry_frontend",
    "icon", "order",   # §7.1 — navigation & presentation, required
)

VALID_COLORS = {
    "blue", "green", "red", "yellow", "orange",
    "purple", "pink", "cyan", "teal", "indigo", "gray",
}

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
DEFAULT_EXPORT_RE = re.compile(
    r"\bexport\s+default\b|\bexport\s*\{[^}]*\bas\s+default\b",
    re.DOTALL,
)


class ModuleCLIValidator:
    """
    Validates a module directory and returns a detailed ValidationReport.

    Usage:
        report = ModuleCLIValidator.validate(Path("modules/installed/hello_world"))
    """

    @staticmethod
    def validate(module_path: Path, platform_version: str = "1.0.0") -> ValidationReport:
        report = ValidationReport(module_path=module_path)

        # ── 1. Directory exists ───────────────────────────────────────────────
        if not module_path.exists() or not module_path.is_dir():
            report.add("Directory exists", False,
                       f"Path not found or not a directory: {module_path}")
            return report
        report.add("Directory exists", True, str(module_path))

        # ── 2. manifest.yaml present ──────────────────────────────────────────
        manifest_file = module_path / "manifest.yaml"
        if not manifest_file.exists():
            report.add("manifest.yaml present", False, "manifest.yaml not found.")
            return report
        report.add("manifest.yaml present", True, str(manifest_file))

        # ── 3. YAML parseable ─────────────────────────────────────────────────
        try:
            import yaml
            raw: dict = yaml.safe_load(manifest_file.read_text(encoding="utf-8")) or {}
        except Exception as exc:
            report.add("manifest.yaml parseable", False, str(exc))
            return report
        report.add("manifest.yaml parseable", True, "Valid YAML")

        # ── 4. Required fields ────────────────────────────────────────────────
        missing = [f for f in REQUIRED_MANIFEST_FIELDS if not raw.get(f)]
        if missing:
            report.add("Required fields", False,
                       f"Missing: {', '.join(missing)}")
        else:
            report.add("Required fields", True,
                       f"All {len(REQUIRED_MANIFEST_FIELDS)} required fields present")

        # ── 5. id format ──────────────────────────────────────────────────────
        module_id = str(raw.get("id", "")).strip()
        id_ok = bool(re.match(r"^[a-z][a-z0-9_]{1,63}$", module_id))
        report.add("Module id format", id_ok,
                   "Valid snake_case id" if id_ok
                   else f"Must be lowercase snake_case, got: {module_id!r}")

        # ── 6. Semver fields ──────────────────────────────────────────────────
        for field_name in ("version", "platform_min_version", "platform_max_version"):
            val = str(raw.get(field_name, "0.0.0"))
            ok = bool(SEMVER_RE.match(val))
            report.add(f"Semver: {field_name}", ok,
                       f"{field_name}={val}" if ok
                       else f"{field_name}={val!r} is not valid semver (X.Y.Z)")

        # ── 7. Required subdirectories ────────────────────────────────────────
        for subdir in ("backend", "frontend"):
            exists = (module_path / subdir).is_dir()
            report.add(f"Directory: {subdir}/", exists,
                       f"{subdir}/ present" if exists
                       else f"Required directory '{subdir}/' is missing")

        for subdir in ("assets", "docs", "tests"):
            exists = (module_path / subdir).is_dir()
            report.add(f"Directory: {subdir}/", exists,
                       f"{subdir}/ present" if exists
                       else f"Optional directory '{subdir}/' is absent",
                       level="warning")

        # ── 8. Entry points exist on disk ─────────────────────────────────────
        for field_name in ("entry_backend", "entry_frontend"):
            entry = raw.get(field_name, "")
            if entry:
                full = module_path / entry
                exists = full.exists()
                report.add(f"Entry point: {field_name}", exists,
                           f"{entry} found" if exists
                           else f"{entry} declared in manifest but not found on disk")

        # ── 9. Platform compatibility ─────────────────────────────────────────
        def vt(v: str) -> tuple:
            try:
                return tuple(int(p) for p in v.split("."))
            except ValueError:
                return (0, 0, 0)

        pv    = vt(platform_version)
        min_v = vt(str(raw.get("platform_min_version", "0.0.0")))
        max_v = vt(str(raw.get("platform_max_version", "999.999.999")))
        compat = min_v <= pv <= max_v
        report.add("Platform compatibility", compat,
                   f"Platform {platform_version} is within "
                   f"[{raw.get('platform_min_version')}, {raw.get('platform_max_version')}]"
                   if compat else
                   f"Platform {platform_version} is OUTSIDE declared range "
                   f"[{raw.get('platform_min_version')}, {raw.get('platform_max_version')}]")

        # ── 9b. icon format ───────────────────────────────────────────────────
        import re as _re
        icon_val = str(raw.get("icon", "")).strip()
        icon_ok = bool(_re.match(r"^[a-z][a-z0-9-]{1,63}$", icon_val)) if icon_val else False
        report.add("icon format", icon_ok,
                   f"icon={icon_val!r} — valid kebab-case lucide name" if icon_ok
                   else f"icon={icon_val!r} — must be kebab-case lucide name (e.g. shield-check)")

        # ── 9c. order is a non-negative integer ────────────────────────────────
        try:
            order_val = int(raw.get("order", -1))
            order_ok = order_val >= 0
        except (ValueError, TypeError):
            order_ok = False
        report.add("order value", order_ok,
                   f"order={raw.get('order')} — valid" if order_ok
                   else f"order must be a non-negative integer, got: {raw.get('order')!r}")

        # ── 9d. color is optional but must be a known design-system value ──────
        color_val = raw.get("color")
        if color_val:
            color_ok = str(color_val).lower() in VALID_COLORS
            report.add("color value", color_ok,
                       f"color={color_val!r} — valid design-system color" if color_ok
                       else f"color={color_val!r} not in allowed set",
                       level="warning")

        # ── 10. Backend contract check (static AST) ───────────────────────────
        backend_file = module_path / str(raw.get("entry_backend", "backend/main.py"))
        if backend_file.exists():
            src = backend_file.read_text(encoding="utf-8")
            has_router   = "router" in src
            has_contract = "ModuleContract" in src
            report.add("Backend: router exported", has_router,
                       "router found" if has_router
                       else "No 'router' found — Plugin Loader requires a FastAPI router")
            report.add("Backend: ModuleContract", has_contract,
                       "ModuleContract implemented" if has_contract
                       else "ModuleContract not used — implement lifecycle hooks",
                       level="warning")

        # ── 11. Frontend contract check (static text search) ─────────────────
        frontend_file = module_path / str(raw.get("entry_frontend", "frontend/index.tsx"))
        if frontend_file.exists():
            src = frontend_file.read_text(encoding="utf-8")
            has_config  = "moduleConfig" in src
            has_default = bool(DEFAULT_EXPORT_RE.search(src))
            report.add("Frontend: moduleConfig exported", has_config,
                       "moduleConfig found" if has_config
                       else "moduleConfig not exported — Core cannot register the module")
            report.add("Frontend: default component", has_default,
                       "Default export found" if has_default
                       else "No default export — Plugin Loader needs a default React component")

        # ── 12. §16 Documentation First Principle ──────────────────────────────
        ModuleCLIValidator._check_documentation_first(report, module_path, raw)

        # ── 13. §8.1 Dependency Governance ──────────────────────────────────────
        ModuleCLIValidator._check_dependency_governance(report, raw)

        # ── 14. §10.6 Integrity ──────────────────────────────────────────────────
        integrity_status = ModuleCLIValidator._check_integrity(report, module_path)

        # ── 15. §10.11 Signature ───────────────────────────────────────────────
        ModuleCLIValidator._check_signature(report, raw)

        # ── 16. §10.8 Trust Level ──────────────────────────────────────────────
        ModuleCLIValidator._check_trust(report, integrity_status)

        return report

    @staticmethod
    def _check_documentation_first(report: ValidationReport, module_path: Path, raw: dict) -> None:
        """
        §16 — Documentation First Principle.

        A module is not "done" without: Implementation + Contract + Documentation
        + Example. Service modules (module_type: service) additionally require
        a complete contract (every export typed, with returns and examples) and
        all three example tiers (basic, advanced, integration).
        """
        module_type = str(raw.get("module_type", "application")).strip().lower()
        is_service  = module_type == "service"
        docs_dir    = module_path / "docs"

        # ── Documentation: overview.md ────────────────────────────────────────
        overview = docs_dir / "overview.md"
        overview_ok = overview.exists() and len(overview.read_text(encoding="utf-8").strip()) > 40
        report.add("Documentation: overview.md", overview_ok,
                   "docs/overview.md present and non-trivial" if overview_ok
                   else "docs/overview.md missing or too short — required by the Documentation First Principle")

        # ── Example: at least basic.md is mandatory for every module ──────────
        examples_dir = docs_dir / "examples"
        basic_exists = (examples_dir / "basic.md").exists()
        report.add("Example: basic.md", basic_exists,
                   "docs/examples/basic.md present" if basic_exists
                   else "docs/examples/basic.md missing — every module must provide at least one functional example")

        # ── Service modules: contract completeness + all 3 example tiers ──────
        if not is_service:
            return

        contract_path = docs_dir / "contracts" / "api.yaml"
        if not contract_path.exists():
            report.add("Contract: api.yaml present", False,
                       "module_type is 'service' but docs/contracts/api.yaml is missing")
        else:
            report.add("Contract: api.yaml present", True, str(contract_path))
            ModuleCLIValidator._check_contract_completeness(report, contract_path)

        for tier in ("advanced.md", "integration.md"):
            exists = (examples_dir / tier).exists()
            report.add(f"Example: {tier}", exists,
                       f"docs/examples/{tier} present" if exists
                       else f"docs/examples/{tier} missing — required for service modules (module_type: service)")

    @staticmethod
    def _check_dependency_governance(report: ValidationReport, raw: dict) -> None:
        """
        §8.1 — Dependency Governance: estrutura, duplicidade e direção
        (Service Module não pode depender de Application Module). Reusa
        DependencyValidator — sem duplicar a lógica aqui.
        """
        dependencies = raw.get("dependencies") or []
        if not dependencies:
            return

        module_type = str(raw.get("module_type", "application")).strip().lower()

        module_registry = None
        try:
            from app.module_engine.registry import registry as module_registry
        except Exception:
            module_registry = None

        from app.dependency_engine.validator import DependencyValidator
        checks = DependencyValidator.validate(module_type, dependencies, module_registry=module_registry)
        for c in checks:
            report.add(f"Dependencies: {c.name}", c.passed, c.detail,
                       level="error" if c.required else "warning")

    @staticmethod
    def _check_integrity(report: ValidationReport, module_path: Path):
        """
        §10.6 — verifica integrity.json se já existir (típico de um
        diretório JÁ INSTALADO, gerado por PackageManager.install()).
        Um diretório de código-fonte ainda não empacotado/instalado
        legitimamente não tem integrity.json — isso não é uma falha,
        é o estado esperado antes da instalação. Retorna o
        IntegrityStatus resolvido, ou None se não havia o que checar.
        """
        from app.module_trust.integrity import INTEGRITY_FILENAME, IntegrityStatus, verify_integrity

        integrity_file = module_path / INTEGRITY_FILENAME
        if not integrity_file.is_file():
            report.add("Integrity: manifest present", True,
                       "integrity.json not yet generated — expected before installation",
                       level="warning")
            return None

        result = verify_integrity(module_path)
        passed = result.status == IntegrityStatus.VALID
        detail = result.detail or (
            f"modified={result.modified_files}, missing={result.missing_files}, "
            f"unexpected={result.unexpected_files}"
        )
        report.add(f"Integrity: {result.status.value}", passed,
                   "all files match integrity.json" if passed else detail)
        return result.status

    @staticmethod
    def _check_signature(report: ValidationReport, raw: dict) -> None:
        """§10.11 — este validador é síncrono/standalone (sem AsyncSession,
        não consulta o Publisher Registry — mesma limitação de `_check_trust`
        abaixo), então nunca tem a `public_key` pra verificar de verdade.
        Reporta honestamente NOT_CONFIGURED nesse caso (Fase 17: antes da
        Ed25519SignatureProvider real, uma assinatura presente reportava o
        status enganoso UNSUPPORTED, como se não houvesse algoritmo — hoje
        há, só falta a chave). Só uma assinatura explicitamente INVALID
        (verificável apenas via GET /modules/{id}/trust, com DB) bloqueia."""
        import base64

        from app.module_trust.signature import (
            SignatureStatus,
            canonical_manifest_bytes,
            default_signature_provider,
        )

        signature = raw.get("signature")
        signature_bytes = base64.b64decode(signature) if signature else None
        status = default_signature_provider.verify(
            data=canonical_manifest_bytes(raw), signature=signature_bytes, public_key=None)
        report.add(f"Signature: {status.value}", status != SignatureStatus.INVALID,
                   f"signature status: {status.value}", level="warning")

    @staticmethod
    def _check_trust(report: ValidationReport, integrity_status) -> None:
        """
        §10.8 — Trust Level. Limitação conhecida e documentada: este
        validador roda de forma síncrona (sem sessão de banco), então
        não consulta o Publisher Registry (que exige AsyncSession) —
        o resultado aqui nunca chega a VERIFIED/TRUSTED, só reflete a
        dimensão de integridade. A resolução completa (com publisher
        real) acontece na API assíncrona (GET /modules/{id}/trust).
        Só roda se houver integrity_status pra avaliar (diretório já
        instalado) — pular silenciosamente pra diretório-fonte ainda
        não instalado não é um erro.
        """
        if integrity_status is None:
            return

        from app.module_trust.trust import TrustResolver

        level = TrustResolver.resolve(integrity_status, publisher=None)
        report.add(f"Trust Level: {level.value}", True,
                   f"{level.value} (publisher not checked — synchronous validator, "
                   f"see GET /modules/{{id}}/trust for full resolution)",
                   level="warning")

    @staticmethod
    def _check_contract_completeness(report: ValidationReport, contract_path: Path) -> None:
        """
        §16 — every export in api.yaml must declare: name, description,
        parameters (each with type + required), returns, and examples.
        """
        try:
            import yaml
            raw_contract = yaml.safe_load(contract_path.read_text(encoding="utf-8")) or {}
        except Exception as exc:
            report.add("Contract: parseable", False, f"api.yaml invalid: {exc}")
            return

        exports = raw_contract.get("exports", [])
        if not exports:
            report.add("Contract: has exports", False,
                       "api.yaml has no entries under 'exports'")
            return
        report.add("Contract: has exports", True, f"{len(exports)} export(s) declared")

        for exp in exports:
            if not isinstance(exp, dict):
                continue
            name = str(exp.get("name", "?"))
            prefix = f"Contract '{name}'"

            report.add(f"{prefix}: name", bool(exp.get("name")),
                       "has name" if exp.get("name") else "missing name")
            report.add(f"{prefix}: description", bool(exp.get("description")),
                       "has description" if exp.get("description") else "missing description")

            params = exp.get("parameters", [])
            params_ok = all(
                isinstance(p, dict) and p.get("type") and "required" in p
                for p in params
            )
            report.add(f"{prefix}: parameters typed", params_ok,
                       f"{len(params)} parameter(s), all typed with required flag" if params_ok
                       else "one or more parameters missing 'type' or 'required'")

            returns = exp.get("returns")
            report.add(f"{prefix}: returns", bool(returns),
                       "has returns" if returns else "missing returns")

            examples = exp.get("examples", [])
            report.add(f"{prefix}: examples", bool(examples),
                       f"{len(examples)} example(s)" if examples else "no examples provided")
