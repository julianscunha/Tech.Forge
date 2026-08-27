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

from fastapi.testclient import TestClient

from app.main import app
from app.module_engine.manifest import ManifestParser
from app.module_engine.registry import ModuleEntry, ModuleStatus
from app.doc_engine.api_yaml_parser import APIYamlParser
from app.doc_engine.models import ServiceContract, ServiceExport
from app.service_registry.descriptor import ServiceDescriptor, ServiceStatus
from app.service_registry.registry import ServiceRegistry


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


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


# ── Slice 2 — ServiceRegistry: rebuild / discovery / conflicts ───────────────

def _module_entry(module_id, module_type="service", status=None):
    from datetime import datetime
    from app.module_engine.registry import ModuleEntry, ModuleStatus
    return ModuleEntry(
        module_id=module_id, name=module_id, version="1.0.0",
        category="C", vendor="V", author="A", description="D",
        status=status or ModuleStatus.INSTALLED, install_date=datetime.now(),
        module_type=module_type,
    )


class _FakeIndexer:
    def __init__(self, contracts: dict[str, ServiceContract]):
        self._contracts = contracts

    def get_contract(self, module_id):
        return self._contracts.get(module_id)


class TestServiceRegistryRebuild:

    def test_registers_service_module_with_contract(self):
        entry = _module_entry("aws_cost_service")
        contract = ServiceContract(
            service_id="aws.costs", module_id="aws_cost_service",
            description="d", version="1.0.0", capabilities=["aws.cost.read"],
        )
        reg = ServiceRegistry()
        reg.rebuild([entry], _FakeIndexer({"aws_cost_service": contract}))

        descriptor = reg.find_service("aws.costs")
        assert descriptor is not None
        assert descriptor.status == ServiceStatus.ACTIVE
        assert descriptor.capabilities == ["aws.cost.read"]

    def test_skips_application_modules(self):
        entry = _module_entry("some_app", module_type="application")
        reg = ServiceRegistry()
        reg.rebuild([entry], _FakeIndexer({}))
        assert reg.list_services() == []

    def test_service_module_without_contract_marked_failed(self):
        entry = _module_entry("broken_service")
        reg = ServiceRegistry()
        reg.rebuild([entry], _FakeIndexer({}))
        descriptor = reg.find_by_module("broken_service")
        assert descriptor is not None
        assert descriptor.status == ServiceStatus.FAILED

    def test_disabled_module_yields_disabled_service(self):
        from app.module_engine.registry import ModuleStatus
        entry = _module_entry("aws_cost_service", status=ModuleStatus.DISABLED)
        contract = ServiceContract(
            service_id="aws.costs", module_id="aws_cost_service",
            description="d", version="1.0.0",
        )
        reg = ServiceRegistry()
        reg.rebuild([entry], _FakeIndexer({"aws_cost_service": contract}))
        assert reg.find_service("aws.costs").status == ServiceStatus.DISABLED

    def test_rebuild_clears_previous_state(self):
        entry = _module_entry("aws_cost_service")
        contract = ServiceContract(service_id="aws.costs", module_id="aws_cost_service",
                                   description="d", version="1.0.0")
        reg = ServiceRegistry()
        reg.rebuild([entry], _FakeIndexer({"aws_cost_service": contract}))
        assert len(reg.list_services()) == 1

        reg.rebuild([], _FakeIndexer({}))
        assert reg.list_services() == []


class TestServiceRegistryDiscovery:

    def _registry_with_two_services(self, same_capability=False):
        e1 = _module_entry("svc_a")
        e2 = _module_entry("svc_b")
        cap = "shared.read" if same_capability else "svc_a.read"
        c1 = ServiceContract(service_id="a", module_id="svc_a", description="d",
                             version="1.0.0", capabilities=[cap])
        c2 = ServiceContract(service_id="b", module_id="svc_b", description="d",
                             version="1.0.0",
                             capabilities=["shared.read"] if same_capability else ["svc_b.read"])
        reg = ServiceRegistry()
        reg.rebuild([e1, e2], _FakeIndexer({"svc_a": c1, "svc_b": c2}))
        return reg

    def test_find_capability_returns_providers(self):
        reg = self._registry_with_two_services()
        providers = reg.find_capability("svc_a.read")
        assert [d.service_id for d in providers] == ["a"]

    def test_list_capabilities_maps_capability_to_service_ids(self):
        reg = self._registry_with_two_services()
        caps = reg.list_capabilities()
        assert caps["svc_a.read"] == ["a"]
        assert caps["svc_b.read"] == ["b"]

    def test_no_conflict_when_capabilities_differ(self):
        reg = self._registry_with_two_services(same_capability=False)
        assert reg.list_conflicts() == {}

    def test_conflict_detected_when_two_active_services_share_capability(self):
        reg = self._registry_with_two_services(same_capability=True)
        conflicts = reg.list_conflicts()
        assert set(conflicts["shared.read"]) == {"a", "b"}


class TestServiceRegistryRealModules:
    """Integração com o boot real da app (hello_world/veeam_m365)."""

    def test_hello_world_registered_as_active_service(self, client):
        from app.service_registry.registry import service_registry
        descriptor = service_registry.find_by_module("hello_world")
        assert descriptor is not None, service_registry.list_services()
        assert descriptor.status == ServiceStatus.ACTIVE
        assert descriptor.capabilities or descriptor.contract is not None

    def test_deactivate_then_activate_updates_service_status(self, client):
        from app.service_registry.registry import service_registry

        client.post("/api/v1/marketplace/activate/hello_world")  # ensure clean baseline

        r1 = client.post("/api/v1/marketplace/deactivate/hello_world")
        assert r1.status_code == 200, r1.text
        assert service_registry.find_by_module("hello_world").status == ServiceStatus.DISABLED

        r2 = client.post("/api/v1/marketplace/activate/hello_world")
        assert r2.status_code == 200, r2.text
        assert service_registry.find_by_module("hello_world").status == ServiceStatus.ACTIVE


# ── Slice 3 — Invocação + validação de argumentos + erros ────────────────────

class TestInvoke:

    def test_invoke_hello_world_ping_returns_documented_result(self, client):
        from app.service_registry.invoker import invoke
        result = invoke("hello_world", "ping")
        assert result == {"module": "hello_world", "status": "ok", "version": "1.0.0"}

    def test_invoke_veeam_calculate_storage_matches_documented_example(self, client):
        from app.service_registry.invoker import invoke
        result = invoke("veeam_m365", "calculate_storage", users=500, mailbox_quota_gb=50)
        assert result["total_gb"] == 25000.0
        assert result["recommended_repo_gb"] == 27500.0

    def test_invoke_unknown_service_raises_service_not_found(self, client):
        from app.service_registry.invoker import invoke
        from app.service_registry.errors import ServiceNotFoundError
        with pytest.raises(ServiceNotFoundError):
            invoke("ghost_service", "ping")

    def test_invoke_unknown_export_raises_capability_not_found(self, client):
        from app.service_registry.invoker import invoke
        from app.service_registry.errors import CapabilityNotFoundError
        with pytest.raises(CapabilityNotFoundError):
            invoke("hello_world", "does_not_exist")

    def test_invoke_missing_required_argument_raises_invalid_arguments(self, client):
        from app.service_registry.invoker import invoke
        from app.service_registry.errors import InvalidArgumentsError
        with pytest.raises(InvalidArgumentsError):
            invoke("veeam_m365", "calculate_storage", mailbox_quota_gb=50)  # missing users

    def test_invoke_unknown_argument_raises_invalid_arguments(self, client):
        from app.service_registry.invoker import invoke
        from app.service_registry.errors import InvalidArgumentsError
        with pytest.raises(InvalidArgumentsError):
            invoke("veeam_m365", "calculate_storage", users=1, mailbox_quota_gb=1, bogus=1)

    def test_invoke_disabled_service_raises_service_disabled(self, client):
        from app.service_registry.invoker import invoke
        from app.service_registry.errors import ServiceDisabledError

        client.post("/api/v1/marketplace/activate/hello_world")  # clean baseline
        client.post("/api/v1/marketplace/deactivate/hello_world")
        try:
            with pytest.raises(ServiceDisabledError):
                invoke("hello_world", "ping")
        finally:
            client.post("/api/v1/marketplace/activate/hello_world")

    def test_invoke_execution_failure_does_not_leak_internal_traceback(self, tmp_path, monkeypatch):
        """A função invocada explode — o chamador só vê o erro tipado, sem stack trace interno."""
        from app.service_registry.registry import ServiceRegistry
        from app.service_registry.descriptor import ServiceDescriptor, ServiceStatus
        from app.service_registry.errors import ServiceExecutionFailedError
        import app.service_registry.invoker as invoker_mod

        contract = ServiceContract(
            service_id="broken", module_id="broken_mod", description="d", version="1.0.0",
            exports=[ServiceExport(name="explode", description="d", parameters=[])],
        )
        descriptor = ServiceDescriptor(
            service_id="broken", module_id="broken_mod", module_version="1.0.0",
            service_version="1.0.0", contract=contract, status=ServiceStatus.ACTIVE,
        )
        fake_registry = ServiceRegistry()
        fake_registry._services["broken"] = descriptor
        monkeypatch.setattr(invoker_mod, "service_registry", fake_registry)

        def _boom(**kwargs):
            raise RuntimeError("some internal secret detail")

        monkeypatch.setattr(invoker_mod, "_load_export_callable", lambda *a, **k: _boom)

        with pytest.raises(ServiceExecutionFailedError) as exc_info:
            invoker_mod.invoke("broken", "explode")
        assert "some internal secret detail" not in str(exc_info.value)
