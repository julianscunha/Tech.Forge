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
