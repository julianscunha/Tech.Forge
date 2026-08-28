"""
Fase 8.1 — Dependency Governance
=================================
Run: pytest core/backend/tests/test_phase8_1_dependency_governance.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))
sys.path.insert(0, str(ROOT / "cli"))

from app.module_engine.manifest import ManifestParser
from app.module_engine.enums import ModuleStatus


def write_manifest(mod: Path, module_id: str = "mod", module_type: str = "application",
                   dependencies: list[dict] | None = None) -> None:
    manifest = {
        "id": module_id, "name": "Module", "version": "1.0.0",
        "platform_min_version": "1.0.0", "platform_max_version": "2.0.0",
        "category": "Test", "vendor": "T", "author": "T",
        "description": "T", "entry_backend": "backend/main.py",
        "entry_frontend": "frontend/index.tsx",
        "icon": "shield-check", "order": 10,
    }
    if module_type != "application":
        manifest["module_type"] = module_type
    if dependencies is not None:
        manifest["dependencies"] = dependencies
    mod.mkdir(parents=True, exist_ok=True)
    (mod / "manifest.yaml").write_text(yaml.dump(manifest), encoding="utf-8")


# ── ModuleStatus.BLOCKED ───────────────────────────────────────────────────────

class TestModuleStatusBlocked:

    def test_blocked_status_exists(self):
        assert ModuleStatus.BLOCKED.value == "BLOCKED"

    def test_blocked_is_distinct_from_disabled(self):
        assert ModuleStatus.BLOCKED != ModuleStatus.DISABLED


# ── ParsedManifest.dependencies (raw pass-through) ────────────────────────────

class TestManifestDependencies:

    def test_defaults_to_empty_list(self, tmp_path):
        mod = tmp_path / "mod"
        write_manifest(mod, "mod")
        manifest = ManifestParser.parse(mod)
        assert manifest.dependencies == []

    def test_parses_module_dependency(self, tmp_path):
        mod = tmp_path / "mod"
        write_manifest(mod, "mod", dependencies=[
            {"target": {"type": "module", "id": "aws_cost_service"},
             "version_range": ">=1.0.0,<2.0.0", "required": True},
        ])
        manifest = ManifestParser.parse(mod)
        assert manifest.dependencies == [
            {"target": {"type": "module", "id": "aws_cost_service"},
             "version_range": ">=1.0.0,<2.0.0", "required": True},
        ]

    def test_parses_capability_dependency(self, tmp_path):
        mod = tmp_path / "mod"
        write_manifest(mod, "mod", dependencies=[
            {"target": {"type": "capability", "id": "aws.cost.read"},
             "version_range": ">=1.0.0", "required": False},
        ])
        manifest = ManifestParser.parse(mod)
        assert manifest.dependencies[0]["target"]["type"] == "capability"


# ── DependencyParser + models ─────────────────────────────────────────────────

class TestDependencyParser:

    def test_parses_module_dependency_into_typed_model(self):
        from app.dependency_engine.parser import DependencyParser
        from app.dependency_engine.models import Dependency, TargetType

        raw = [{"target": {"type": "module", "id": "aws_cost_service"},
               "version_range": ">=1.0.0,<2.0.0", "required": True}]
        deps = DependencyParser.parse(raw)
        assert deps == [Dependency(
            target_type=TargetType.MODULE, target_id="aws_cost_service",
            version_range=">=1.0.0,<2.0.0", required=True,
        )]

    def test_parses_capability_dependency_into_typed_model(self):
        from app.dependency_engine.parser import DependencyParser
        from app.dependency_engine.models import TargetType

        raw = [{"target": {"type": "capability", "id": "aws.cost.read"},
               "version_range": ">=1.0.0", "required": False}]
        deps = DependencyParser.parse(raw)
        assert deps[0].target_type == TargetType.CAPABILITY
        assert deps[0].target_id == "aws.cost.read"
        assert deps[0].required is False

    def test_defaults_required_to_true_when_absent(self):
        from app.dependency_engine.parser import DependencyParser

        raw = [{"target": {"type": "module", "id": "x"}, "version_range": ">=1.0.0"}]
        deps = DependencyParser.parse(raw)
        assert deps[0].required is True

    def test_defaults_version_range_to_any_when_absent(self):
        from app.dependency_engine.parser import DependencyParser

        raw = [{"target": {"type": "module", "id": "x"}}]
        deps = DependencyParser.parse(raw)
        assert deps[0].version_range is None
        assert deps[0].satisfies_version("0.0.1")
        assert deps[0].satisfies_version("999.0.0")

    def test_invalid_version_range_raises(self):
        from app.dependency_engine.parser import DependencyParser, DependencyParseError

        raw = [{"target": {"type": "module", "id": "x"}, "version_range": "not a range"}]
        with pytest.raises(DependencyParseError):
            DependencyParser.parse(raw)

    def test_invalid_target_type_raises(self):
        from app.dependency_engine.parser import DependencyParser, DependencyParseError

        raw = [{"target": {"type": "bogus", "id": "x"}}]
        with pytest.raises(DependencyParseError):
            DependencyParser.parse(raw)

    def test_missing_target_id_raises(self):
        from app.dependency_engine.parser import DependencyParser, DependencyParseError

        raw = [{"target": {"type": "module", "id": ""}}]
        with pytest.raises(DependencyParseError):
            DependencyParser.parse(raw)

    def test_empty_list_parses_to_empty(self):
        from app.dependency_engine.parser import DependencyParser
        assert DependencyParser.parse([]) == []


class TestDependencyVersionSatisfaction:

    def test_satisfies_version_true_within_range(self):
        from app.dependency_engine.models import Dependency, TargetType
        dep = Dependency(target_type=TargetType.MODULE, target_id="x",
                         version_range=">=1.0.0,<2.0.0", required=True)
        assert dep.satisfies_version("1.5.0")

    def test_satisfies_version_false_outside_range(self):
        from app.dependency_engine.models import Dependency, TargetType
        dep = Dependency(target_type=TargetType.MODULE, target_id="x",
                         version_range=">=1.0.0,<2.0.0", required=True)
        assert not dep.satisfies_version("2.0.0")
        assert not dep.satisfies_version("0.9.0")


# ── DependencyValidator (§17) ──────────────────────────────────────────────────

def _entry(module_id: str, module_type: str, status: ModuleStatus = None):
    from datetime import datetime
    from app.module_engine.registry import ModuleEntry
    return ModuleEntry(
        module_id=module_id, name=module_id, version="1.0.0",
        category="C", vendor="V", author="A", description="D",
        status=status or ModuleStatus.INSTALLED, install_date=datetime.now(),
        module_type=module_type,
    )


class _FakeModuleRegistry:
    def __init__(self, entries: dict):
        self._entries = entries

    def get(self, module_id: str):
        return self._entries.get(module_id)


class TestDependencyValidator:

    def test_valid_dependencies_all_pass(self):
        from app.dependency_engine.validator import DependencyValidator

        raw = [{"target": {"type": "module", "id": "aws_sdk_service"},
               "version_range": ">=1.0.0", "required": True}]
        checks = DependencyValidator.validate("application", raw)
        assert all(c.passed for c in checks)

    def test_structurally_invalid_dependency_fails(self):
        from app.dependency_engine.validator import DependencyValidator

        raw = [{"target": {"type": "bogus", "id": "x"}}]
        checks = DependencyValidator.validate("application", raw)
        assert any(not c.passed for c in checks)

    def test_duplicate_target_fails(self):
        from app.dependency_engine.validator import DependencyValidator

        raw = [
            {"target": {"type": "module", "id": "x"}, "required": True},
            {"target": {"type": "module", "id": "x"}, "required": False},
        ]
        checks = DependencyValidator.validate("application", raw)
        dup_checks = [c for c in checks if "duplicate" in c.name.lower()]
        assert dup_checks and not dup_checks[0].passed

    def test_no_duplicate_when_targets_differ(self):
        from app.dependency_engine.validator import DependencyValidator

        raw = [
            {"target": {"type": "module", "id": "x"}},
            {"target": {"type": "capability", "id": "x"}},  # same id, different type — not a dup
        ]
        checks = DependencyValidator.validate("application", raw)
        dup_checks = [c for c in checks if "duplicate" in c.name.lower()]
        assert not dup_checks

    def test_service_depending_on_known_application_module_fails_direction(self):
        from app.dependency_engine.validator import DependencyValidator

        raw = [{"target": {"type": "module", "id": "some_app"}}]
        registry = _FakeModuleRegistry({"some_app": _entry("some_app", "application")})
        checks = DependencyValidator.validate("service", raw, module_registry=registry)
        dir_checks = [c for c in checks if "direction" in c.name.lower()]
        assert dir_checks and not dir_checks[0].passed

    def test_service_depending_on_known_service_module_passes_direction(self):
        from app.dependency_engine.validator import DependencyValidator

        raw = [{"target": {"type": "module", "id": "other_service"}}]
        registry = _FakeModuleRegistry({"other_service": _entry("other_service", "service")})
        checks = DependencyValidator.validate("service", raw, module_registry=registry)
        dir_checks = [c for c in checks if "direction" in c.name.lower()]
        assert dir_checks and dir_checks[0].passed

    def test_application_depending_on_application_does_not_fail_direction(self):
        """Application -> Application nao e a regra proibida (so Service -> Application)."""
        from app.dependency_engine.validator import DependencyValidator

        raw = [{"target": {"type": "module", "id": "other_app"}}]
        registry = _FakeModuleRegistry({"other_app": _entry("other_app", "application")})
        checks = DependencyValidator.validate("application", raw, module_registry=registry)
        dir_checks = [c for c in checks if "direction" in c.name.lower() and not c.passed]
        assert not dir_checks

    def test_direction_skipped_when_target_unknown(self):
        """Sem registry ou alvo nao encontrado — nao da pra validar, nao falha."""
        from app.dependency_engine.validator import DependencyValidator

        raw = [{"target": {"type": "module", "id": "not_installed_yet"}}]
        checks = DependencyValidator.validate("service", raw, module_registry=None)
        dir_checks = [c for c in checks if "direction" in c.name.lower() and not c.passed]
        assert not dir_checks

    def test_capability_dependency_never_triggers_direction_check(self):
        from app.dependency_engine.validator import DependencyValidator

        raw = [{"target": {"type": "capability", "id": "aws.cost.read"}}]
        checks = DependencyValidator.validate("service", raw)
        dir_checks = [c for c in checks if "direction" in c.name.lower() and not c.passed]
        assert not dir_checks


# ── CLI integration — techforge validate-module ──────────────────────────────

def _make_full_module(tmp: Path, module_id: str, module_type: str = "application",
                      dependencies: list[dict] | None = None) -> Path:
    mod = tmp / module_id
    (mod / "backend").mkdir(parents=True)
    (mod / "frontend").mkdir(parents=True)
    (mod / "backend" / "main.py").write_text("router = None", encoding="utf-8")
    (mod / "frontend" / "index.tsx").write_text(
        "export const moduleConfig = {}\nexport default function() {}", encoding="utf-8")
    write_manifest(mod, module_id, module_type, dependencies)
    return mod


class TestCLIDependencyGovernance:

    def test_valid_dependency_passes_validation(self, tmp_path):
        from techforge_cli.validators.module_validator import ModuleCLIValidator
        mod = _make_full_module(tmp_path, "app_mod", dependencies=[
            {"target": {"type": "capability", "id": "aws.cost.read"}, "required": False},
        ])
        report = ModuleCLIValidator.validate(mod)
        dep_checks = [c for c in report.checks if c.name.startswith("§8.1")]
        assert dep_checks
        assert all(c.passed for c in dep_checks)

    def test_structurally_invalid_dependency_fails_validation(self, tmp_path):
        from techforge_cli.validators.module_validator import ModuleCLIValidator
        mod = _make_full_module(tmp_path, "app_mod", dependencies=[
            {"target": {"type": "bogus", "id": "x"}},
        ])
        report = ModuleCLIValidator.validate(mod)
        assert not report.passed

    def test_no_dependencies_declared_does_not_add_checks(self, tmp_path):
        from techforge_cli.validators.module_validator import ModuleCLIValidator
        mod = _make_full_module(tmp_path, "app_mod")
        report = ModuleCLIValidator.validate(mod)
        dep_checks = [c for c in report.checks if c.name.startswith("§8.1")]
        assert dep_checks == []


# ── DependencyGraph (§6/§27) ───────────────────────────────────────────────────

class _FakeServiceRegistry:
    def __init__(self, capability_providers: dict | None = None):
        self._capability_providers = capability_providers or {}

    def find_capability(self, capability: str):
        return self._capability_providers.get(capability, [])


class _FakeProvider:
    def __init__(self, module_id: str):
        self.module_id = module_id


def _entry_with_deps(module_id: str, dependencies: list[dict],
                     module_type: str = "application"):
    entry = _entry(module_id, module_type)
    entry.manifest_raw = {"dependencies": dependencies}
    return entry


class _AllEntriesRegistry:
    def __init__(self, entries: list):
        self._entries = {e.module_id: e for e in entries}

    def all(self):
        return list(self._entries.values())

    def get(self, module_id):
        return self._entries.get(module_id)


class TestDependencyGraph:

    def test_module_dependency_becomes_edge(self):
        from app.dependency_engine.graph import DependencyGraph

        a = _entry_with_deps("a", [{"target": {"type": "module", "id": "b"}}])
        b = _entry_with_deps("b", [])
        graph = DependencyGraph.build(_AllEntriesRegistry([a, b]), _FakeServiceRegistry())

        assert any(e.source == "a" and e.target == "b" and e.kind == "module"
                  for e in graph.edges)

    def test_capability_dependency_resolves_to_provider_module(self):
        from app.dependency_engine.graph import DependencyGraph

        consumer = _entry_with_deps("consumer", [
            {"target": {"type": "capability", "id": "aws.cost.read"}},
        ])
        registry = _AllEntriesRegistry([consumer])
        services = _FakeServiceRegistry({"aws.cost.read": [_FakeProvider("aws_cost_service")]})
        graph = DependencyGraph.build(registry, services)

        assert any(e.source == "consumer" and e.target == "aws_cost_service"
                  and e.kind == "capability" for e in graph.edges)

    def test_no_dependencies_produces_no_edges(self):
        from app.dependency_engine.graph import DependencyGraph

        a = _entry_with_deps("a", [])
        graph = DependencyGraph.build(_AllEntriesRegistry([a]), _FakeServiceRegistry())
        assert graph.edges == []

    def test_acyclic_graph_has_valid_topological_order(self):
        from app.dependency_engine.graph import DependencyGraph

        a = _entry_with_deps("a", [{"target": {"type": "module", "id": "b"}}])
        b = _entry_with_deps("b", [{"target": {"type": "module", "id": "c"}}])
        c = _entry_with_deps("c", [])
        graph = DependencyGraph.build(_AllEntriesRegistry([a, b, c]), _FakeServiceRegistry())

        order = graph.topological_order()
        assert order.index("c") < order.index("b") < order.index("a")
        assert graph.detect_cycles() == []

    def test_cyclic_graph_detects_full_cycle_path(self):
        from app.dependency_engine.graph import DependencyGraph

        a = _entry_with_deps("a", [{"target": {"type": "module", "id": "b"}}])
        b = _entry_with_deps("b", [{"target": {"type": "module", "id": "c"}}])
        c = _entry_with_deps("c", [{"target": {"type": "module", "id": "a"}}])
        graph = DependencyGraph.build(_AllEntriesRegistry([a, b, c]), _FakeServiceRegistry())

        cycles = graph.detect_cycles()
        assert len(cycles) == 1
        cycle = cycles[0]
        assert cycle[0] == cycle[-1]
        assert {"a", "b", "c"} <= set(cycle)

    def test_export_mermaid_produces_flowchart_syntax(self):
        from app.dependency_engine.graph import DependencyGraph

        a = _entry_with_deps("a", [{"target": {"type": "module", "id": "b"}}])
        b = _entry_with_deps("b", [])
        graph = DependencyGraph.build(_AllEntriesRegistry([a, b]), _FakeServiceRegistry())

        mermaid = graph.export_mermaid()
        assert mermaid.startswith("flowchart TD")
        assert "a -->|module| b" in mermaid

    def test_export_mermaid_highlights_cycle_nodes(self):
        from app.dependency_engine.graph import DependencyGraph

        a = _entry_with_deps("a", [{"target": {"type": "module", "id": "b"}}])
        b = _entry_with_deps("b", [{"target": {"type": "module", "id": "a"}}])
        graph = DependencyGraph.build(_AllEntriesRegistry([a, b]), _FakeServiceRegistry())

        mermaid = graph.export_mermaid()
        assert "classDef cycle" in mermaid
        assert "class a,b cycle" in mermaid


# ── DependencyResolver (§7/§8/§15/§23) ─────────────────────────────────────────

class _FakeDescriptor:
    def __init__(self, module_id: str, service_version: str = "1.0.0", status=None):
        from app.service_registry.descriptor import ServiceStatus
        self.module_id = module_id
        self.service_version = service_version
        self.status = status or ServiceStatus.ACTIVE


class _FakeServiceRegistryFull:
    def __init__(self, capability_providers: dict | None = None, conflicts: dict | None = None):
        self._capability_providers = capability_providers or {}
        self._conflicts = conflicts or {}

    def find_capability(self, capability: str):
        return self._capability_providers.get(capability, [])

    def list_conflicts(self):
        return self._conflicts


class TestDependencyResolver:

    def test_module_dependency_satisfied(self):
        from app.dependency_engine.resolver import DependencyResolver
        from app.dependency_engine.models import DependencyStatus

        consumer = _entry_with_deps("consumer", [
            {"target": {"type": "module", "id": "provider"}, "version_range": ">=1.0.0"},
        ])
        provider = _entry_with_deps("provider", [])
        provider.version = "1.5.0"
        registry = _AllEntriesRegistry([consumer, provider])

        deps = DependencyResolver.resolve("consumer", registry, _FakeServiceRegistryFull())
        assert deps[0].status == DependencyStatus.SATISFIED

    def test_module_dependency_missing_when_not_installed(self):
        from app.dependency_engine.resolver import DependencyResolver
        from app.dependency_engine.models import DependencyStatus

        consumer = _entry_with_deps("consumer", [
            {"target": {"type": "module", "id": "nowhere"}, "required": True},
        ])
        registry = _AllEntriesRegistry([consumer])

        deps = DependencyResolver.resolve("consumer", registry, _FakeServiceRegistryFull())
        assert deps[0].status == DependencyStatus.MISSING

    def test_module_dependency_optional_unavailable_when_not_installed(self):
        from app.dependency_engine.resolver import DependencyResolver
        from app.dependency_engine.models import DependencyStatus

        consumer = _entry_with_deps("consumer", [
            {"target": {"type": "module", "id": "nowhere"}, "required": False},
        ])
        registry = _AllEntriesRegistry([consumer])

        deps = DependencyResolver.resolve("consumer", registry, _FakeServiceRegistryFull())
        assert deps[0].status == DependencyStatus.OPTIONAL_UNAVAILABLE

    def test_module_dependency_disabled(self):
        from app.dependency_engine.resolver import DependencyResolver
        from app.dependency_engine.models import DependencyStatus

        consumer = _entry_with_deps("consumer", [
            {"target": {"type": "module", "id": "provider"}, "required": True},
        ])
        provider = _entry_with_deps("provider", [], )
        provider.status = ModuleStatus.DISABLED
        registry = _AllEntriesRegistry([consumer, provider])

        deps = DependencyResolver.resolve("consumer", registry, _FakeServiceRegistryFull())
        assert deps[0].status == DependencyStatus.DISABLED

    def test_module_dependency_incompatible_version(self):
        from app.dependency_engine.resolver import DependencyResolver
        from app.dependency_engine.models import DependencyStatus

        consumer = _entry_with_deps("consumer", [
            {"target": {"type": "module", "id": "provider"}, "version_range": ">=2.0.0"},
        ])
        provider = _entry_with_deps("provider", [])
        provider.version = "1.0.0"
        registry = _AllEntriesRegistry([consumer, provider])

        deps = DependencyResolver.resolve("consumer", registry, _FakeServiceRegistryFull())
        assert deps[0].status == DependencyStatus.INCOMPATIBLE_VERSION

    def test_module_dependency_cyclic(self):
        from app.dependency_engine.resolver import DependencyResolver
        from app.dependency_engine.models import DependencyStatus

        a = _entry_with_deps("a", [{"target": {"type": "module", "id": "b"}}])
        b = _entry_with_deps("b", [{"target": {"type": "module", "id": "a"}}])
        registry = _AllEntriesRegistry([a, b])

        deps = DependencyResolver.resolve("a", registry, _FakeServiceRegistryFull())
        assert deps[0].status == DependencyStatus.CYCLIC

    def test_capability_dependency_satisfied(self):
        from app.dependency_engine.resolver import DependencyResolver
        from app.dependency_engine.models import DependencyStatus

        consumer = _entry_with_deps("consumer", [
            {"target": {"type": "capability", "id": "aws.cost.read"}, "version_range": ">=1.0.0"},
        ])
        registry = _AllEntriesRegistry([consumer])
        services = _FakeServiceRegistryFull({"aws.cost.read": [_FakeDescriptor("aws_cost_service")]})

        deps = DependencyResolver.resolve("consumer", registry, services)
        assert deps[0].status == DependencyStatus.SATISFIED

    def test_capability_dependency_missing_when_no_provider(self):
        from app.dependency_engine.resolver import DependencyResolver
        from app.dependency_engine.models import DependencyStatus

        consumer = _entry_with_deps("consumer", [
            {"target": {"type": "capability", "id": "aws.cost.read"}, "required": True},
        ])
        registry = _AllEntriesRegistry([consumer])

        deps = DependencyResolver.resolve("consumer", registry, _FakeServiceRegistryFull())
        assert deps[0].status == DependencyStatus.MISSING

    def test_capability_dependency_disabled_when_provider_inactive(self):
        from app.dependency_engine.resolver import DependencyResolver
        from app.dependency_engine.models import DependencyStatus
        from app.service_registry.descriptor import ServiceStatus

        consumer = _entry_with_deps("consumer", [
            {"target": {"type": "capability", "id": "aws.cost.read"}, "required": True},
        ])
        registry = _AllEntriesRegistry([consumer])
        services = _FakeServiceRegistryFull({
            "aws.cost.read": [_FakeDescriptor("aws_cost_service", status=ServiceStatus.DISABLED)],
        })

        deps = DependencyResolver.resolve("consumer", registry, services)
        assert deps[0].status == DependencyStatus.DISABLED

    def test_capability_dependency_conflict_when_multiple_active_providers(self):
        from app.dependency_engine.resolver import DependencyResolver
        from app.dependency_engine.models import DependencyStatus

        consumer = _entry_with_deps("consumer", [
            {"target": {"type": "capability", "id": "shared.read"}, "required": True},
        ])
        registry = _AllEntriesRegistry([consumer])
        services = _FakeServiceRegistryFull(
            capability_providers={"shared.read": [_FakeDescriptor("a"), _FakeDescriptor("b")]},
            conflicts={"shared.read": ["a", "b"]},
        )

        deps = DependencyResolver.resolve("consumer", registry, services)
        assert deps[0].status == DependencyStatus.CONFLICT

    def test_capability_dependency_incompatible_version(self):
        from app.dependency_engine.resolver import DependencyResolver
        from app.dependency_engine.models import DependencyStatus

        consumer = _entry_with_deps("consumer", [
            {"target": {"type": "capability", "id": "aws.cost.read"}, "version_range": ">=2.0.0"},
        ])
        registry = _AllEntriesRegistry([consumer])
        services = _FakeServiceRegistryFull(
            {"aws.cost.read": [_FakeDescriptor("aws_cost_service", service_version="1.0.0")]})

        deps = DependencyResolver.resolve("consumer", registry, services)
        assert deps[0].status == DependencyStatus.INCOMPATIBLE_VERSION

    def test_capability_dependency_optional_unavailable_when_no_provider(self):
        from app.dependency_engine.resolver import DependencyResolver
        from app.dependency_engine.models import DependencyStatus

        consumer = _entry_with_deps("consumer", [
            {"target": {"type": "capability", "id": "aws.cost.read"}, "required": False},
        ])
        registry = _AllEntriesRegistry([consumer])

        deps = DependencyResolver.resolve("consumer", registry, _FakeServiceRegistryFull())
        assert deps[0].status == DependencyStatus.OPTIONAL_UNAVAILABLE

    def test_unknown_module_returns_empty_list(self):
        from app.dependency_engine.resolver import DependencyResolver

        registry = _AllEntriesRegistry([])
        deps = DependencyResolver.resolve("ghost", registry, _FakeServiceRegistryFull())
        assert deps == []


# ── Lifecycle hooks (§10/§11/§12/§13/§14) ──────────────────────────────────────

class TestCheckCanActivate:

    def test_blocks_when_required_module_dependency_missing(self):
        from app.dependency_engine.lifecycle import check_can_activate

        consumer = _entry_with_deps("consumer", [
            {"target": {"type": "module", "id": "provider"}, "required": True},
        ])
        registry = _AllEntriesRegistry([consumer])

        can, blocking = check_can_activate("consumer", registry, _FakeServiceRegistryFull())
        assert can is False
        assert len(blocking) == 1

    def test_allows_when_required_dependency_satisfied(self):
        from app.dependency_engine.lifecycle import check_can_activate

        consumer = _entry_with_deps("consumer", [
            {"target": {"type": "module", "id": "provider"}, "required": True},
        ])
        provider = _entry_with_deps("provider", [])
        registry = _AllEntriesRegistry([consumer, provider])

        can, blocking = check_can_activate("consumer", registry, _FakeServiceRegistryFull())
        assert can is True
        assert blocking == []

    def test_optional_unavailable_dependency_does_not_block(self):
        from app.dependency_engine.lifecycle import check_can_activate

        consumer = _entry_with_deps("consumer", [
            {"target": {"type": "module", "id": "nowhere"}, "required": False},
        ])
        registry = _AllEntriesRegistry([consumer])

        can, blocking = check_can_activate("consumer", registry, _FakeServiceRegistryFull())
        assert can is True
        assert blocking == []


class TestCheckCanDeactivate:

    def test_blocks_when_installed_dependent_requires_it_via_module(self):
        from app.dependency_engine.lifecycle import check_can_deactivate

        provider = _entry_with_deps("provider", [])
        consumer = _entry_with_deps("consumer", [
            {"target": {"type": "module", "id": "provider"}, "required": True},
        ])
        registry = _AllEntriesRegistry([provider, consumer])

        can, dependents = check_can_deactivate("provider", registry, _FakeServiceRegistryFull())
        assert can is False
        assert dependents == ["consumer"]

    def test_blocks_when_installed_dependent_requires_it_via_capability(self):
        from app.dependency_engine.lifecycle import check_can_deactivate

        provider = _entry_with_deps("provider", [])
        consumer = _entry_with_deps("consumer", [
            {"target": {"type": "capability", "id": "aws.cost.read"}, "required": True},
        ])
        registry = _AllEntriesRegistry([provider, consumer])
        services = _FakeServiceRegistryFull({"aws.cost.read": [_FakeDescriptor("provider")]})

        can, dependents = check_can_deactivate("provider", registry, services)
        assert can is False
        assert dependents == ["consumer"]

    def test_allows_when_no_installed_dependents(self):
        from app.dependency_engine.lifecycle import check_can_deactivate

        provider = _entry_with_deps("provider", [])
        registry = _AllEntriesRegistry([provider])

        can, dependents = check_can_deactivate("provider", registry, _FakeServiceRegistryFull())
        assert can is True
        assert dependents == []

    def test_allows_when_dependent_is_optional(self):
        from app.dependency_engine.lifecycle import check_can_deactivate

        provider = _entry_with_deps("provider", [])
        consumer = _entry_with_deps("consumer", [
            {"target": {"type": "module", "id": "provider"}, "required": False},
        ])
        registry = _AllEntriesRegistry([provider, consumer])

        can, dependents = check_can_deactivate("provider", registry, _FakeServiceRegistryFull())
        assert can is True

    def test_allows_when_dependent_is_disabled(self):
        from app.dependency_engine.lifecycle import check_can_deactivate

        provider = _entry_with_deps("provider", [])
        consumer = _entry_with_deps("consumer", [
            {"target": {"type": "module", "id": "provider"}, "required": True},
        ])
        consumer.status = ModuleStatus.DISABLED
        registry = _AllEntriesRegistry([provider, consumer])

        can, dependents = check_can_deactivate("provider", registry, _FakeServiceRegistryFull())
        assert can is True


class TestCheckCanRemove:

    def test_mirrors_check_can_deactivate(self):
        from app.dependency_engine.lifecycle import check_can_remove

        provider = _entry_with_deps("provider", [])
        consumer = _entry_with_deps("consumer", [
            {"target": {"type": "module", "id": "provider"}, "required": True},
        ])
        registry = _AllEntriesRegistry([provider, consumer])

        can, dependents = check_can_remove("provider", registry, _FakeServiceRegistryFull())
        assert can is False
        assert dependents == ["consumer"]


# ── API routes (§25) ───────────────────────────────────────────────────────────

@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as c:
        yield c


class TestDependencyAPIRoutes:

    def test_get_dependencies_of_module_without_declarations(self, client):
        resp = client.get("/api/v1/modules/hello_world/dependencies")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_dependents_of_module_without_dependents(self, client):
        resp = client.get("/api/v1/modules/hello_world/dependents")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_validate_endpoint_returns_dict(self, client):
        resp = client.get("/api/v1/dependencies/validate")
        assert resp.status_code == 200
        assert isinstance(resp.json(), dict)

    def test_graph_endpoint_returns_mermaid(self, client):
        resp = client.get("/api/v1/dependencies/graph")
        assert resp.status_code == 200
        assert resp.json()["mermaid"].startswith("flowchart TD")


# ── CLI commands (§24) ──────────────────────────────────────────────────────────

class TestDependencyCLI:

    def test_dependencies_command_registered(self):
        from techforge_cli.commands.modules import modules_cmd
        assert "dependencies" in modules_cmd.commands
        assert "dependents" in modules_cmd.commands
        assert "validate-dependencies" in modules_cmd.commands
        assert "graph" in modules_cmd.commands
