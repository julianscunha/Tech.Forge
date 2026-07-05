"""
TechForge §16 — Documentation First Principle Test Suite
============================================================
Tests:
  - DocCompletenessChecker (backend)
  - CLI validate-module §16 checks (application vs service modules)
  - TemplateGenerator produces §16-compliant scaffolds by default
  - Real modules (hello_world, veeam_m365) are 100% complete
  - api.yaml `returns` normalization (string vs {type: X})

Run: pytest core/backend/tests/test_documentation_first.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))
sys.path.insert(0, str(ROOT / "cli"))
sys.path.insert(0, str(ROOT / "sdk" / "python"))

from app.doc_engine.completeness import (
    DocCompletenessChecker, validate_contract_completeness, DoDCheck,
)
from app.doc_engine.api_yaml_parser import APIYamlParser, _normalize_returns
from app.doc_engine.models import ServiceContract, ServiceExport


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_module(
    tmp: Path,
    module_id: str = "test_mod",
    module_type: str = "application",
    with_overview: bool = True,
    with_basic_example: bool = True,
    with_advanced_example: bool = False,
    with_integration_example: bool = False,
    with_contract: bool = False,
    contract_complete: bool = True,
) -> Path:
    """Build a module directory with configurable §16 compliance."""
    mod = tmp / module_id
    (mod / "backend").mkdir(parents=True)
    (mod / "frontend").mkdir(parents=True)
    (mod / "docs" / "examples").mkdir(parents=True)

    (mod / "backend" / "main.py").write_text("router = None", encoding="utf-8")
    (mod / "frontend" / "index.tsx").write_text(
        "export const moduleConfig = {}\nexport default function() {}",
        encoding="utf-8",
    )

    if with_overview:
        (mod / "docs" / "overview.md").write_text(
            "# Test Module\n\nThis is a sufficiently long overview for the checker.",
            encoding="utf-8",
        )

    if with_basic_example:
        (mod / "docs" / "examples" / "basic.md").write_text("## Objetivo\n\nBasic.", encoding="utf-8")
    if with_advanced_example:
        (mod / "docs" / "examples" / "advanced.md").write_text("## Objetivo\n\nAdvanced.", encoding="utf-8")
    if with_integration_example:
        (mod / "docs" / "examples" / "integration.md").write_text("## Objetivo\n\nIntegration.", encoding="utf-8")

    if with_contract:
        contracts_dir = mod / "docs" / "contracts"
        contracts_dir.mkdir()
        if contract_complete:
            data = {
                "service_id": module_id,
                "description": "A complete test service.",
                "version": "1.0.0",
                "exports": [{
                    "name": "do_thing",
                    "description": "Does a thing.",
                    "parameters": [
                        {"name": "x", "type": "int", "required": True, "description": "Input"},
                    ],
                    "returns": {"type": "str"},
                    "examples": ["do_thing(1) → 'one'"],
                }],
            }
        else:
            # Incomplete: missing returns and examples
            data = {
                "service_id": module_id,
                "description": "An incomplete test service.",
                "version": "1.0.0",
                "exports": [{
                    "name": "broken_thing",
                    "description": "",   # missing description too
                    "parameters": [{"name": "x"}],  # missing type/required
                }],
            }
        (contracts_dir / "api.yaml").write_text(yaml.dump(data), encoding="utf-8")

    manifest = {
        "id": module_id, "name": "Test Module", "version": "1.0.0",
        "platform_min_version": "1.0.0", "platform_max_version": "2.0.0",
        "category": "Test", "vendor": "T", "author": "T",
        "description": "T", "entry_backend": "backend/main.py",
        "entry_frontend": "frontend/index.tsx",
        "icon": "shield-check", "order": 10,
    }
    if module_type != "application":
        manifest["module_type"] = module_type
    (mod / "manifest.yaml").write_text(yaml.dump(manifest), encoding="utf-8")

    return mod


# ── DocCompletenessChecker — application modules ──────────────────────────────

class TestCompletenessApplicationModules:

    def test_complete_application_module_passes(self, tmp_path):
        mod = make_module(tmp_path, "app_mod", module_type="application")
        report = DocCompletenessChecker.check(mod, "application")
        assert report.is_complete
        assert report.score == 100.0

    def test_missing_overview_fails(self, tmp_path):
        mod = make_module(tmp_path, "app_mod", with_overview=False)
        report = DocCompletenessChecker.check(mod, "application")
        assert not report.is_complete
        assert any("overview" in m.lower() for m in report.missing)

    def test_missing_basic_example_fails(self, tmp_path):
        mod = make_module(tmp_path, "app_mod", with_basic_example=False)
        report = DocCompletenessChecker.check(mod, "application")
        assert not report.is_complete
        assert any("basic" in m.lower() for m in report.missing)

    def test_missing_backend_fails(self, tmp_path):
        mod = make_module(tmp_path, "app_mod")
        (mod / "backend" / "main.py").unlink()
        report = DocCompletenessChecker.check(mod, "application")
        assert not report.is_complete

    def test_application_module_without_contract_still_complete(self, tmp_path):
        """Contract is only recommended (not required) for application modules."""
        mod = make_module(tmp_path, "app_mod", with_contract=False)
        report = DocCompletenessChecker.check(mod, "application")
        assert report.is_complete

    def test_application_module_does_not_need_advanced_or_integration(self, tmp_path):
        mod = make_module(tmp_path, "app_mod",
                          with_advanced_example=False, with_integration_example=False)
        report = DocCompletenessChecker.check(mod, "application")
        assert report.is_complete

    def test_score_partial_when_missing_one_required_check(self, tmp_path):
        mod = make_module(tmp_path, "app_mod", with_overview=False)
        report = DocCompletenessChecker.check(mod, "application")
        assert 0 < report.score < 100


# ── DocCompletenessChecker — service modules ──────────────────────────────────

class TestCompletenessServiceModules:

    def test_complete_service_module_passes(self, tmp_path):
        mod = make_module(
            tmp_path, "svc_mod", module_type="service",
            with_advanced_example=True, with_integration_example=True,
            with_contract=True, contract_complete=True,
        )
        report = DocCompletenessChecker.check(mod, "service")
        assert report.is_complete, report.missing
        assert report.score == 100.0

    def test_service_without_contract_fails(self, tmp_path):
        mod = make_module(tmp_path, "svc_mod", module_type="service", with_contract=False)
        report = DocCompletenessChecker.check(mod, "service")
        assert not report.is_complete
        assert any("contract" in m.lower() for m in report.missing)

    def test_service_with_incomplete_contract_fails(self, tmp_path):
        mod = make_module(
            tmp_path, "svc_mod", module_type="service",
            with_contract=True, contract_complete=False,
            with_advanced_example=True, with_integration_example=True,
        )
        report = DocCompletenessChecker.check(mod, "service")
        assert not report.is_complete

    def test_service_missing_advanced_example_fails(self, tmp_path):
        mod = make_module(
            tmp_path, "svc_mod", module_type="service",
            with_contract=True, contract_complete=True,
            with_advanced_example=False, with_integration_example=True,
        )
        report = DocCompletenessChecker.check(mod, "service")
        assert not report.is_complete
        assert any("advanced" in m.lower() for m in report.missing)

    def test_service_missing_integration_example_fails(self, tmp_path):
        mod = make_module(
            tmp_path, "svc_mod", module_type="service",
            with_contract=True, contract_complete=True,
            with_advanced_example=True, with_integration_example=False,
        )
        report = DocCompletenessChecker.check(mod, "service")
        assert not report.is_complete
        assert any("integration" in m.lower() for m in report.missing)

    def test_application_module_not_held_to_service_example_tiers(self, tmp_path):
        """An application module without advanced/integration examples is still complete."""
        mod = make_module(tmp_path, "app_mod", module_type="application")
        report = DocCompletenessChecker.check(mod, "application")
        advanced_check = next(c for c in report.checks if "advanced.md" in c.name)
        assert advanced_check.required is False


# ── Contract completeness validation ──────────────────────────────────────────

class TestContractCompleteness:

    def test_none_contract_fails(self):
        checks = validate_contract_completeness(None)
        assert any(not c.passed for c in checks)

    def test_contract_without_exports_fails(self):
        contract = ServiceContract(
            service_id="x", module_id="x", description="desc", version="1.0.0", exports=[],
        )
        checks = validate_contract_completeness(contract)
        assert any("exports" in c.name.lower() and not c.passed for c in checks)

    def test_export_missing_description_fails(self):
        contract = ServiceContract(
            service_id="x", module_id="x", description="d", version="1.0.0",
            exports=[ServiceExport(name="fn", description="", parameters=[],
                                   returns="str", examples=["fn()"])],
        )
        checks = validate_contract_completeness(contract)
        desc_check = next(c for c in checks if "description" in c.name)
        assert not desc_check.passed

    def test_export_missing_returns_fails(self):
        contract = ServiceContract(
            service_id="x", module_id="x", description="d", version="1.0.0",
            exports=[ServiceExport(name="fn", description="desc", parameters=[],
                                   returns=None, examples=["fn()"])],
        )
        checks = validate_contract_completeness(contract)
        returns_check = next(c for c in checks if "returns" in c.name)
        assert not returns_check.passed

    def test_export_missing_examples_fails(self):
        contract = ServiceContract(
            service_id="x", module_id="x", description="d", version="1.0.0",
            exports=[ServiceExport(name="fn", description="desc", parameters=[],
                                   returns="str", examples=[])],
        )
        checks = validate_contract_completeness(contract)
        examples_check = next(c for c in checks if "examples" in c.name)
        assert not examples_check.passed

    def test_export_param_without_type_fails(self):
        contract = ServiceContract(
            service_id="x", module_id="x", description="d", version="1.0.0",
            exports=[ServiceExport(
                name="fn", description="desc",
                parameters=[{"name": "x", "required": True}],   # missing type
                returns="str", examples=["fn(1)"],
            )],
        )
        checks = validate_contract_completeness(contract)
        param_check = next(c for c in checks if "parameters typed" in c.name)
        assert not param_check.passed

    def test_fully_complete_export_passes_all(self):
        contract = ServiceContract(
            service_id="x", module_id="x", description="d", version="1.0.0",
            exports=[ServiceExport(
                name="fn", description="desc",
                parameters=[{"name": "x", "type": "int", "required": True, "description": "in"}],
                returns="str", examples=["fn(1) → '1'"],
            )],
        )
        checks = validate_contract_completeness(contract)
        assert all(c.passed for c in checks)


# ── returns normalization (official §16 spec format) ─────────────────────────

class TestReturnsNormalization:

    def test_plain_string(self):
        assert _normalize_returns("str") == "str"

    def test_typed_dict_format(self):
        assert _normalize_returns({"type": "CostSummary[]"}) == "CostSummary[]"

    def test_none_returns_none(self):
        assert _normalize_returns(None) is None

    def test_empty_dict_returns_none(self):
        assert _normalize_returns({}) is None

    def test_parser_handles_typed_returns(self, tmp_path):
        api_yaml = tmp_path / "api.yaml"
        api_yaml.write_text(yaml.dump({
            "service_id": "svc", "description": "d", "version": "1.0.0",
            "exports": [{
                "name": "get_monthly_costs",
                "description": "Retorna custos mensais consolidados.",
                "parameters": [
                    {"name": "start_date", "type": "date", "required": True},
                    {"name": "end_date", "type": "date", "required": True},
                ],
                "returns": {"type": "CostSummary[]"},
            }],
        }), encoding="utf-8")
        contract = APIYamlParser.parse(api_yaml, "svc")
        assert contract.exports[0].returns == "CostSummary[]"

    def test_parser_handles_plain_string_returns(self, tmp_path):
        api_yaml = tmp_path / "api.yaml"
        api_yaml.write_text(yaml.dump({
            "service_id": "svc", "description": "d", "version": "1.0.0",
            "exports": [{"name": "fn", "description": "d", "returns": "str"}],
        }), encoding="utf-8")
        contract = APIYamlParser.parse(api_yaml, "svc")
        assert contract.exports[0].returns == "str"


# ── TemplateGenerator — §16 compliance by default ─────────────────────────────

class TestTemplateGeneratorDocumentationFirst:

    def _spec(self):
        from techforge_cli.templates.generator import ModuleSpec
        return ModuleSpec(
            id="gen_mod", name="Generated Module", category="Test",
            vendor="T", author="T", description="Generated for testing.",
        )

    def test_generated_module_has_overview(self, tmp_path):
        from techforge_cli.templates.generator import TemplateGenerator
        gen = TemplateGenerator(tmp_path)
        mod = gen.generate(self._spec())
        assert (mod / "docs" / "overview.md").exists()

    def test_generated_module_has_basic_example(self, tmp_path):
        from techforge_cli.templates.generator import TemplateGenerator
        gen = TemplateGenerator(tmp_path)
        mod = gen.generate(self._spec())
        assert (mod / "docs" / "examples" / "basic.md").exists()

    def test_generated_module_passes_completeness_check(self, tmp_path):
        from techforge_cli.templates.generator import TemplateGenerator
        gen = TemplateGenerator(tmp_path)
        mod = gen.generate(self._spec())
        report = DocCompletenessChecker.check(mod, "application")
        assert report.is_complete, report.missing

    def test_generated_module_passes_cli_validation(self, tmp_path):
        from techforge_cli.templates.generator import TemplateGenerator
        from techforge_cli.validators.module_validator import ModuleCLIValidator
        gen = TemplateGenerator(tmp_path)
        mod = gen.generate(self._spec())
        report = ModuleCLIValidator.validate(mod)
        errors = [c for c in report.checks if not c.passed and c.level == "error"]
        assert not errors, [c.message for c in errors]


# ── Real installed modules — must be 100% §16 complete ────────────────────────

class TestRealModulesCompliance:

    def test_hello_world_is_complete(self):
        mod_path = ROOT / "modules" / "installed" / "hello_world"
        report = DocCompletenessChecker.check(mod_path, "service")
        assert report.is_complete, report.missing
        assert report.score == 100.0

    def test_veeam_m365_is_complete(self):
        mod_path = ROOT / "modules" / "installed" / "veeam_m365"
        report = DocCompletenessChecker.check(mod_path, "service")
        assert report.is_complete, report.missing
        assert report.score == 100.0

    def test_hello_world_has_all_three_example_tiers(self):
        examples = ROOT / "modules" / "installed" / "hello_world" / "docs" / "examples"
        assert (examples / "basic.md").exists()
        assert (examples / "advanced.md").exists()
        assert (examples / "integration.md").exists()

    def test_veeam_m365_has_all_three_example_tiers(self):
        examples = ROOT / "modules" / "installed" / "veeam_m365" / "docs" / "examples"
        assert (examples / "basic.md").exists()
        assert (examples / "advanced.md").exists()
        assert (examples / "integration.md").exists()

    def test_hello_world_contract_is_complete(self):
        contract_path = (ROOT / "modules" / "installed" / "hello_world"
                         / "docs" / "contracts" / "api.yaml")
        contract = APIYamlParser.parse(contract_path, "hello_world")
        checks = validate_contract_completeness(contract)
        failures = [c for c in checks if not c.passed]
        assert not failures, [c.detail for c in failures]

    def test_veeam_m365_contract_is_complete(self):
        contract_path = (ROOT / "modules" / "installed" / "veeam_m365"
                         / "docs" / "contracts" / "api.yaml")
        contract = APIYamlParser.parse(contract_path, "veeam_m365")
        checks = validate_contract_completeness(contract)
        failures = [c for c in checks if not c.passed]
        assert not failures, [c.detail for c in failures]

    def test_veeam_m365_calculate_storage_matches_documented_example(self):
        """The basic.md example output must match what the real function returns."""
        import asyncio, importlib.util

        backend_path = ROOT / "modules" / "installed" / "veeam_m365" / "backend" / "main.py"
        spec = importlib.util.spec_from_file_location("veeam_main", backend_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        result = asyncio.run(mod.module.calculate_storage(users=500, mailbox_quota_gb=50))
        # As documented in docs/examples/basic.md
        assert result["total_gb"] == 25000.0
        assert result["recommended_repo_gb"] == 27500.0
        assert result["growth_factor"] == 1.1


# ── CLI validate-module — §16 checks present in report ────────────────────────

class TestCLIValidatorDocumentationFirst:

    def test_application_module_without_overview_fails_validation(self, tmp_path):
        from techforge_cli.validators.module_validator import ModuleCLIValidator
        mod = make_module(tmp_path, "no_overview", with_overview=False)
        report = ModuleCLIValidator.validate(mod)
        overview_check = next(c for c in report.checks if "overview" in c.name.lower())
        assert not overview_check.passed

    def test_application_module_without_basic_example_fails_validation(self, tmp_path):
        from techforge_cli.validators.module_validator import ModuleCLIValidator
        mod = make_module(tmp_path, "no_basic", with_basic_example=False)
        report = ModuleCLIValidator.validate(mod)
        basic_check = next(c for c in report.checks if "basic.md" in c.name)
        assert not basic_check.passed

    def test_service_module_without_contract_fails_validation(self, tmp_path):
        from techforge_cli.validators.module_validator import ModuleCLIValidator
        mod = make_module(tmp_path, "svc_no_contract", module_type="service",
                         with_contract=False, with_advanced_example=True,
                         with_integration_example=True)
        report = ModuleCLIValidator.validate(mod)
        contract_check = next(c for c in report.checks if "Contract: api.yaml" in c.name)
        assert not contract_check.passed

    def test_service_module_complete_passes_validation(self, tmp_path):
        from techforge_cli.validators.module_validator import ModuleCLIValidator
        mod = make_module(
            tmp_path, "svc_complete", module_type="service",
            with_contract=True, contract_complete=True,
            with_advanced_example=True, with_integration_example=True,
        )
        report = ModuleCLIValidator.validate(mod)
        section16_checks = [c for c in report.checks if c.name.startswith("§16")]
        assert len(section16_checks) > 0
        failures = [c for c in section16_checks if not c.passed and c.level == "error"]
        assert not failures, [c.message for c in failures]

    def test_application_module_not_required_to_have_contract(self, tmp_path):
        from techforge_cli.validators.module_validator import ModuleCLIValidator
        mod = make_module(tmp_path, "app_no_contract", module_type="application",
                         with_contract=False)
        report = ModuleCLIValidator.validate(mod)
        assert report.passed
