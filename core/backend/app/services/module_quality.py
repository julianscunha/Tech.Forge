"""Fase 15 §44/§45 — Module Quality / Release Readiness (por módulo).

Reusa os validadores já existentes (Fases 4, 7, 10, 12) e o extrator de
exemplos executáveis (Slice 4) — não recalcula nada em paralelo (spec §2).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.core.settings import settings
from app.doc_engine.api_yaml_parser import APIYamlParser
from app.doc_engine.completeness import DocCompletenessChecker
from app.doc_engine.contract_examples import extract_example_calls
from app.module_engine.enums import ModuleStatus
from app.module_engine.registry import registry
from app.package_manager.compatibility import check_compatibility
from app.package_manager.enums import CompatibilityLevel
from app.services.release_readiness import ReleaseCheck


class ModuleNotFoundError(Exception):
    pass


@dataclass
class ModuleQualityReport:
    module_id: str
    checks: list[ReleaseCheck] = field(default_factory=list)

    @property
    def ready(self) -> bool:
        return all(c.passed for c in self.checks)


def _check_status(module_id: str) -> ReleaseCheck:
    entry = registry.get(module_id)
    if entry.status in (ModuleStatus.INSTALLED, ModuleStatus.DISABLED):
        return ReleaseCheck("status", True, entry.status.value)
    return ReleaseCheck("status", False, f"status={entry.status.value}")


def _check_documentation(module_id: str) -> ReleaseCheck:
    entry = registry.get(module_id)
    module_path = settings.MODULES_INSTALLED_PATH / module_id
    module_type = (entry.manifest_raw or {}).get("module_type", "application")
    report = DocCompletenessChecker.check(module_path, module_type)
    if report.is_complete:
        return ReleaseCheck("documentation", True, f"score={report.score:.0f}%")
    missing = [c.name for c in report.checks if c.required and not c.passed]
    return ReleaseCheck("documentation", False, f"faltando: {missing}")


def _check_compatibility(module_id: str) -> ReleaseCheck:
    entry = registry.get(module_id)
    manifest = entry.manifest_raw or {}
    min_v = manifest.get("platform_min_version", "0.0.0")
    max_v = manifest.get("platform_max_version", "999.999.999")
    level = check_compatibility(settings.PLATFORM_VERSION, min_v, max_v)
    passed = level != CompatibilityLevel.INCOMPATIBLE
    return ReleaseCheck("compatibility", passed, f"{level.value} (core={settings.PLATFORM_VERSION})")


def _check_contract(module_id: str) -> ReleaseCheck:
    api_yaml = settings.MODULES_INSTALLED_PATH / module_id / "docs" / "contracts" / "api.yaml"
    if not api_yaml.exists():
        return ReleaseCheck("contract", True, "módulo não declara contrato de serviço")

    contract = APIYamlParser.parse(api_yaml, module_id)
    if contract is None:
        return ReleaseCheck("contract", False, "api.yaml presente mas inválido")

    from app.service_registry.descriptor import ServiceStatus
    from app.service_registry.invoker import invoke
    from app.service_registry.registry import service_registry

    descriptor = service_registry.find_service(contract.service_id)
    if descriptor is None or descriptor.status != ServiceStatus.ACTIVE:
        return ReleaseCheck("contract", True, "serviço não está ativo — exemplos não executados")

    checked = 0
    for export in contract.exports:
        for kwargs in extract_example_calls(export):
            checked += 1
            try:
                result = invoke(contract.service_id, export.name, **kwargs)
            except Exception as exc:
                return ReleaseCheck("contract", False, f"{export.name}({kwargs}) levantou {exc}")
            if result is None:
                return ReleaseCheck("contract", False, f"{export.name}({kwargs}) retornou None")
    return ReleaseCheck("contract", True, f"{checked} exemplo(s) executado(s) com sucesso")


def compute_module_quality(module_id: str) -> ModuleQualityReport:
    if registry.get(module_id) is None:
        raise ModuleNotFoundError(module_id)

    report = ModuleQualityReport(module_id=module_id)
    report.checks.append(_check_status(module_id))
    report.checks.append(_check_documentation(module_id))
    report.checks.append(_check_compatibility(module_id))
    report.checks.append(_check_contract(module_id))
    return report
