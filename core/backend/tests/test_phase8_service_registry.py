"""
Fase 8 — Service Registry
==========================
Run: pytest core/backend/tests/test_phase8_service_registry.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))

from app.module_engine.manifest import ManifestParser
from app.module_engine.registry import ModuleEntry, ModuleStatus
from app.doc_engine.api_yaml_parser import APIYamlParser
from app.doc_engine.models import ServiceContract
from app.service_registry.descriptor import ServiceDescriptor, ServiceStatus


def write_manifest(mod: Path, module_id: str = "svc_mod", module_type: str | None = "service") -> None:
    manifest = {
        "id": module_id, "name": "Service Module", "version": "1.0.0",
        "platform_min_version": "1.0.0", "platform_max_version": "2.0.0",
        "category": "Test", "vendor": "T", "author": "T",
        "description": "T", "entry_backend": "backend/main.py",
        "entry_frontend": "frontend/index.tsx",
        "icon": "shield-check", "order": 10,
    }
    if module_type is not None:
        manifest["module_type"] = module_type
    mod.mkdir(parents=True, exist_ok=True)
    (mod / "manifest.yaml").write_text(yaml.dump(manifest), encoding="utf-8")


# ── Slice 1 — ParsedManifest / ModuleEntry.module_type ────────────────────────

class TestManifestModuleType:

    def test_defaults_to_application_when_absent(self, tmp_path):
        mod = tmp_path / "app_mod"
        write_manifest(mod, "app_mod", module_type=None)
        manifest = ManifestParser.parse(mod)
        assert manifest.module_type == "application"

    def test_parses_service_type(self, tmp_path):
        mod = tmp_path / "svc_mod"
        write_manifest(mod, "svc_mod", module_type="service")
        manifest = ManifestParser.parse(mod)
        assert manifest.module_type == "service"


class TestModuleEntryModuleType:

    def test_from_manifest_carries_module_type(self, tmp_path):
        mod = tmp_path / "svc_mod"
        write_manifest(mod, "svc_mod", module_type="service")
        manifest = ManifestParser.parse(mod)
        entry = ModuleEntry.from_manifest(manifest, ModuleStatus.INSTALLED, [], [])
        assert entry.module_type == "service"

    def test_from_manifest_defaults_application(self, tmp_path):
        mod = tmp_path / "app_mod"
        write_manifest(mod, "app_mod", module_type=None)
        manifest = ManifestParser.parse(mod)
        entry = ModuleEntry.from_manifest(manifest, ModuleStatus.INSTALLED, [], [])
        assert entry.module_type == "application"


# ── Slice 1 — capabilities no api.yaml ────────────────────────────────────────

class TestContractCapabilities:

    def test_parses_capabilities_list(self, tmp_path):
        api_yaml = tmp_path / "api.yaml"
        api_yaml.write_text(yaml.dump({
            "service_id": "svc", "description": "d", "version": "1.0.0",
            "capabilities": ["aws.cost.read", "aws.cost.summary"],
            "exports": [],
        }), encoding="utf-8")
        contract = APIYamlParser.parse(api_yaml, "svc")
        assert contract.capabilities == ["aws.cost.read", "aws.cost.summary"]

    def test_capabilities_default_to_empty_list(self, tmp_path):
        api_yaml = tmp_path / "api.yaml"
        api_yaml.write_text(yaml.dump({
            "service_id": "svc", "description": "d", "version": "1.0.0",
            "exports": [],
        }), encoding="utf-8")
        contract = APIYamlParser.parse(api_yaml, "svc")
        assert contract.capabilities == []


# ── Slice 1 — ServiceDescriptor / ServiceStatus ───────────────────────────────

class TestServiceDescriptor:

    def _contract(self):
        return ServiceContract(
            service_id="aws.costs", module_id="aws_cost_service",
            description="d", version="1.0.0",
            capabilities=["aws.cost.read"],
        )

    def test_defaults_to_registered_status(self):
        descriptor = ServiceDescriptor(
            service_id="aws.costs", module_id="aws_cost_service",
            module_version="1.2.0", service_version="1.0.0",
            capabilities=["aws.cost.read"], contract=self._contract(),
        )
        assert descriptor.status == ServiceStatus.REGISTERED

    def test_all_statuses_exist(self):
        names = {s.name for s in ServiceStatus}
        assert names == {"REGISTERED", "ACTIVE", "UNAVAILABLE", "DISABLED", "FAILED", "REMOVED"}

    def test_to_dict_is_serializable_without_contract_internals(self):
        descriptor = ServiceDescriptor(
            service_id="aws.costs", module_id="aws_cost_service",
            module_version="1.2.0", service_version="1.0.0",
            capabilities=["aws.cost.read"], contract=self._contract(),
            status=ServiceStatus.ACTIVE,
        )
        data = descriptor.to_dict()
        assert data["service_id"] == "aws.costs"
        assert data["module_id"] == "aws_cost_service"
        assert data["status"] == "ACTIVE"
        assert data["capabilities"] == ["aws.cost.read"]
        assert isinstance(data["contract"], dict)
