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

pytestmark = pytest.mark.integration


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

    def _fake_registry_with_parameterized_export(self, monkeypatch):
        """Nenhum módulo de referência real tem export com parâmetros
        obrigatórios (hello_world.ping/info não recebem nada) — registry
        isolado com um export sintético, sem depender de módulo em disco."""
        from app.service_registry.registry import ServiceRegistry
        from app.service_registry.descriptor import ServiceDescriptor, ServiceStatus
        import app.service_registry.invoker as invoker_mod

        contract = ServiceContract(
            service_id="calc", module_id="calc_mod", description="d", version="1.0.0",
            exports=[ServiceExport(
                name="do_thing", description="d",
                parameters=[{"name": "x", "type": "int", "required": True}],
            )],
        )
        descriptor = ServiceDescriptor(
            service_id="calc", module_id="calc_mod", module_version="1.0.0",
            service_version="1.0.0", contract=contract, status=ServiceStatus.ACTIVE,
        )
        fake_registry = ServiceRegistry()
        fake_registry._services["calc"] = descriptor
        monkeypatch.setattr(invoker_mod, "service_registry", fake_registry)
        monkeypatch.setattr(invoker_mod, "_load_export_callable", lambda *a, **k: (lambda **kw: kw))

    def test_invoke_missing_required_argument_raises_invalid_arguments(self, monkeypatch):
        from app.service_registry.invoker import invoke
        from app.service_registry.errors import InvalidArgumentsError
        self._fake_registry_with_parameterized_export(monkeypatch)
        with pytest.raises(InvalidArgumentsError):
            invoke("calc", "do_thing")  # missing required "x"

    def test_invoke_unknown_argument_raises_invalid_arguments(self, monkeypatch):
        from app.service_registry.invoker import invoke
        from app.service_registry.errors import InvalidArgumentsError
        self._fake_registry_with_parameterized_export(monkeypatch)
        with pytest.raises(InvalidArgumentsError):
            invoke("calc", "do_thing", x=1, bogus=1)

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


# ── Slice 4 — API /services* ──────────────────────────────────────────────────

class TestServicesAPI:

    def test_list_services_includes_hello_world(self, client):
        resp = client.get("/api/v1/services")
        assert resp.status_code == 200
        ids = [s["service_id"] for s in resp.json()]
        assert "hello_world" in ids

    def test_get_service_by_id(self, client):
        resp = client.get("/api/v1/services/hello_world")
        assert resp.status_code == 200
        assert resp.json()["module_id"] == "hello_world"

    def test_get_unknown_service_404(self, client):
        resp = client.get("/api/v1/services/ghost_service")
        assert resp.status_code == 404

    def test_get_service_contract(self, client):
        resp = client.get("/api/v1/services/hello_world/contract")
        assert resp.status_code == 200
        names = [e["name"] for e in resp.json()["exports"]]
        assert "ping" in names

    def test_list_capabilities(self, client):
        resp = client.get("/api/v1/services/capabilities")
        assert resp.status_code == 200
        assert isinstance(resp.json(), dict)

    def test_get_capability_providers(self, client):
        resp = client.get("/api/v1/services/capabilities/hello_world.ping")
        assert resp.status_code == 200
        providers = [s["service_id"] for s in resp.json()]
        assert "hello_world" in providers

    def test_get_unknown_capability_returns_empty_list(self, client):
        resp = client.get("/api/v1/services/capabilities/ghost.capability")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_invoke_endpoint_returns_export_result(self, client):
        resp = client.post("/api/v1/services/hello_world/invoke/ping", json={})
        assert resp.status_code == 200
        assert resp.json() == {"module": "hello_world", "status": "ok", "version": "1.0.0"}

    def test_invoke_endpoint_passes_kwargs(self, client, monkeypatch):
        import app.service_registry.invoker as invoker_mod
        from app.service_registry.registry import ServiceRegistry
        from app.service_registry.descriptor import ServiceDescriptor, ServiceStatus

        contract = ServiceContract(
            service_id="calc", module_id="calc_mod", description="d", version="1.0.0",
            exports=[ServiceExport(
                name="do_thing", description="d",
                parameters=[{"name": "x", "type": "int", "required": True}],
            )],
        )
        fake_registry = ServiceRegistry()
        fake_registry._services["calc"] = ServiceDescriptor(
            service_id="calc", module_id="calc_mod", module_version="1.0.0",
            service_version="1.0.0", contract=contract, status=ServiceStatus.ACTIVE,
        )
        monkeypatch.setattr(invoker_mod, "service_registry", fake_registry)
        monkeypatch.setattr(invoker_mod, "_load_export_callable", lambda *a, **k: (lambda **kw: kw))

        resp = client.post("/api/v1/services/calc/invoke/do_thing", json={"x": 7})
        assert resp.status_code == 200
        assert resp.json() == {"x": 7}

    def test_invoke_endpoint_unknown_service_returns_404(self, client):
        resp = client.post("/api/v1/services/ghost_service/invoke/ping", json={})
        assert resp.status_code == 404
        assert resp.json()["detail"]["code"] == "SERVICE_NOT_FOUND"

    def test_invoke_endpoint_unknown_export_returns_404(self, client):
        resp = client.post("/api/v1/services/hello_world/invoke/does_not_exist", json={})
        assert resp.status_code == 404
        assert resp.json()["detail"]["code"] == "CAPABILITY_NOT_FOUND"

    def test_invoke_endpoint_missing_argument_returns_422(self, client, monkeypatch):
        import app.service_registry.invoker as invoker_mod
        from app.service_registry.registry import ServiceRegistry
        from app.service_registry.descriptor import ServiceDescriptor, ServiceStatus

        contract = ServiceContract(
            service_id="calc", module_id="calc_mod", description="d", version="1.0.0",
            exports=[ServiceExport(
                name="do_thing", description="d",
                parameters=[{"name": "x", "type": "int", "required": True}],
            )],
        )
        fake_registry = ServiceRegistry()
        fake_registry._services["calc"] = ServiceDescriptor(
            service_id="calc", module_id="calc_mod", module_version="1.0.0",
            service_version="1.0.0", contract=contract, status=ServiceStatus.ACTIVE,
        )
        monkeypatch.setattr(invoker_mod, "service_registry", fake_registry)
        monkeypatch.setattr(invoker_mod, "_load_export_callable", lambda *a, **k: (lambda **kw: kw))

        resp = client.post("/api/v1/services/calc/invoke/do_thing", json={})
        assert resp.status_code == 422
        assert resp.json()["detail"]["code"] == "INVALID_ARGUMENTS"


class TestDocsContractsExposeCapabilities:
    """Fase 7's /docs/contracts route (consumida pelo Developer Center) deve
    carregar o campo capabilities novo da Fase 8 — sem isso o frontend nao
    consegue exibir capabilities no ServiceContractPanel."""

    def test_docs_contracts_include_capabilities(self, client):
        resp = client.get("/api/v1/docs/contracts/hello_world")
        assert resp.status_code == 200
        assert resp.json()["capabilities"] == ["hello_world.ping", "hello_world.info"]


# ── Slice 6 — AI Context inclui capabilities/status ───────────────────────────

class TestAIContextServiceRegistry:

    def test_ai_context_includes_service_capabilities_and_status(self, client):
        import asyncio
        from app.service_registry import sync as sync_service_registry
        asyncio.run(sync_service_registry())

        resp = client.get("/api/v1/docs/export/ai-context")
        assert resp.status_code == 200
        text = resp.text
        assert "hello_world.ping" in text
        assert "**Status:** ACTIVE" in text


class TestConflictNotification:

    def test_conflict_notifies_once_with_dedupe(self, client, tmp_path, monkeypatch):
        import asyncio
        from app.module_engine.registry import ModuleEntry, ModuleStatus
        from app.service_registry.registry import ServiceRegistry
        import app.service_registry.registry as registry_mod

        e1 = _module_entry("conflict_a")
        e2 = _module_entry("conflict_b")
        c1 = ServiceContract(service_id="a", module_id="conflict_a", description="d",
                             version="1.0.0", capabilities=["shared.read"])
        c2 = ServiceContract(service_id="b", module_id="conflict_b", description="d",
                             version="1.0.0", capabilities=["shared.read"])
        fake_indexer = _FakeIndexer({"conflict_a": c1, "conflict_b": c2})

        reg = ServiceRegistry()
        monkeypatch.setattr(registry_mod, "service_registry", reg)

        async def _run():
            from sqlalchemy import delete
            from app.db.database import AsyncSessionLocal
            from app.models.notifications import Notification
            from app.service_registry.registry import sync_with_notifications

            async with AsyncSessionLocal() as db:
                # Leftover from a previous run would make dedupe skip this
                # run's notification too — clean the exact row first.
                await db.execute(delete(Notification).where(
                    Notification.title == "Capability conflict",
                    Notification.message == "Capability 'shared.read' provided by: a, b"))
                await db.commit()

                await sync_with_notifications([e1, e2], fake_indexer, db)
                await sync_with_notifications([e1, e2], fake_indexer, db)  # repeat — must dedupe

        before_count = client.get("/api/v1/notifications/unread-count").json()["count"]
        asyncio.run(_run())
        after_count = client.get("/api/v1/notifications/unread-count").json()["count"]
        assert after_count == before_count + 1

        notifs = client.get("/api/v1/notifications?limit=5").json()
        assert any("shared.read" in (n.get("message") or "") for n in notifs)
        client.post("/api/v1/notifications/read-all")


# ── Slice 7 — Regra final (spec §28/"Regra final") ────────────────────────────

class TestFullLifecycleIntegration:
    """
    Install → Activate → Registry discovers service → Capability available →
    Application resolves capability → Invoke → Result → Deactivate →
    Capability unavailable → Reactivate → Remove → Registry cleanup.

    Usa hello_world (já instalado) como Service Module real de teste — não é
    necessário criar um módulo novo (spec §29 / decisão do plano).
    """

    def test_full_lifecycle_hello_world(self, client):
        from app.service_registry.registry import service_registry
        from app.service_registry.invoker import invoke

        client.post("/api/v1/marketplace/activate/hello_world")  # clean baseline

        # 1. Registry discovers the service (boot already did this) + capability available
        descriptor = service_registry.find_by_module("hello_world")
        assert descriptor is not None and descriptor.status.value == "ACTIVE"
        providers = service_registry.find_capability("hello_world.ping")
        assert [d.service_id for d in providers] == ["hello_world"]

        # 2. "Application Module" resolves the capability and invokes it
        result = invoke("hello_world", "ping")
        assert result == {"module": "hello_world", "status": "ok", "version": "1.0.0"}

        # 3. Invalid arguments are rejected before reaching the function
        from app.service_registry.errors import InvalidArgumentsError
        with pytest.raises(InvalidArgumentsError):
            invoke("hello_world", "ping", bogus_arg=1)

        # 4. Deactivate → capability unavailable for invocation
        r = client.post("/api/v1/marketplace/deactivate/hello_world")
        assert r.status_code == 200, r.text
        assert service_registry.find_by_module("hello_world").status.value == "DISABLED"
        from app.service_registry.errors import ServiceDisabledError
        with pytest.raises(ServiceDisabledError):
            invoke("hello_world", "ping")

        # 5. Reactivate → capability available again
        r = client.post("/api/v1/marketplace/activate/hello_world")
        assert r.status_code == 200, r.text
        assert service_registry.find_by_module("hello_world").status.value == "ACTIVE"
        assert invoke("hello_world", "ping")["status"] == "ok"

    def test_hot_reload_reindexes_docs_before_service_sync(self, client):
        """Regressão real: reinstalar um Service Module sem reiniciar o app
        deixava o Service Registry preso em FAILED pra sempre. Causa:
        _hot_reload() chamava sync_service_registry() (que lê o contrato via
        doc_indexer.get_contract(), cache in-memory) sem nunca reindexar a
        documentação antes — o cache do contrato só existia se já tivesse
        sido populado no boot; qualquer reinstalação subsequente achava
        cache vazio e marcava FAILED mesmo com docs/contracts/api.yaml
        válido em disco."""
        from app.doc_engine import doc_indexer
        from app.package_manager import package_manager
        from app.service_registry.registry import service_registry

        client.post("/api/v1/marketplace/activate/hello_world")  # clean baseline

        # Simula o estado de "acabou de reinstalar, doc index ainda não
        # sabe do contrato" — remove só o cache, sem tocar no disco.
        doc_indexer._contracts.pop("hello_world", None)

        import asyncio
        asyncio.run(package_manager._hot_reload())

        descriptor = service_registry.find_by_module("hello_world")
        assert descriptor is not None
        assert descriptor.status.value == "ACTIVE"
        assert descriptor.contract is not None

    def test_capability_conflict_reported_not_silently_resolved(self):
        """Dois serviços disputando a mesma capability — Registry reporta, não escolhe."""
        e1 = _module_entry("svc_x")
        e2 = _module_entry("svc_y")
        c1 = ServiceContract(service_id="x", module_id="svc_x", description="d",
                             version="1.0.0", capabilities=["disputed.read"])
        c2 = ServiceContract(service_id="y", module_id="svc_y", description="d",
                             version="1.0.0", capabilities=["disputed.read"])
        reg = ServiceRegistry()
        reg.rebuild([e1, e2], _FakeIndexer({"svc_x": c1, "svc_y": c2}))

        conflicts = reg.list_conflicts()
        assert set(conflicts["disputed.read"]) == {"x", "y"}
        # Both providers remain independently discoverable — no silent pick
        assert {d.service_id for d in reg.find_capability("disputed.read")} == {"x", "y"}


# ── Follow-up — busca por capability/export (discovery em escala) ────────────

class TestServiceRegistrySearch:

    def _registry_with_aws_and_veeam(self):
        e1 = _module_entry("aws_cost_service")
        e2 = _module_entry("other_service")
        c1 = ServiceContract(
            service_id="aws.costs", module_id="aws_cost_service", description="d",
            version="1.0.0", capabilities=["aws.cost.read"],
            exports=[ServiceExport(name="get_cost_summary",
                                   description="Returns cloud cost summary.")],
        )
        c2 = ServiceContract(
            service_id="other", module_id="other_service", description="d", version="1.0.0",
            capabilities=["other.thing"],
            exports=[ServiceExport(name="do_other_thing", description="Unrelated.")],
        )
        reg = ServiceRegistry()
        reg.rebuild([e1, e2], _FakeIndexer({"aws_cost_service": c1, "other_service": c2}))
        return reg

    def test_search_matches_capability(self):
        reg = self._registry_with_aws_and_veeam()
        results = reg.search("cost")
        assert [d.service_id for d in results] == ["aws.costs"]

    def test_search_matches_export_name(self):
        reg = self._registry_with_aws_and_veeam()
        results = reg.search("get_cost_summary")
        assert [d.service_id for d in results] == ["aws.costs"]

    def test_search_matches_export_description(self):
        reg = self._registry_with_aws_and_veeam()
        results = reg.search("cloud")
        assert [d.service_id for d in results] == ["aws.costs"]

    def test_search_is_case_insensitive(self):
        reg = self._registry_with_aws_and_veeam()
        results = reg.search("AWS")
        assert [d.service_id for d in results] == ["aws.costs"]

    def test_search_no_match_returns_empty_list(self):
        reg = self._registry_with_aws_and_veeam()
        assert reg.search("nonexistent_term_xyz") == []

    def test_search_matches_service_id(self):
        reg = self._registry_with_aws_and_veeam()
        results = reg.search("aws.costs")
        assert [d.service_id for d in results] == ["aws.costs"]


class TestServicesAPISearch:

    def test_list_services_with_query_filters(self, client):
        resp = client.get("/api/v1/services?q=hello_world")
        assert resp.status_code == 200
        ids = [s["service_id"] for s in resp.json()]
        assert ids == ["hello_world"]

    def test_list_services_without_query_returns_all(self, client):
        resp = client.get("/api/v1/services")
        assert resp.status_code == 200
        ids = [s["service_id"] for s in resp.json()]
        assert "hello_world" in ids

    def test_list_services_query_no_match_returns_empty(self, client):
        resp = client.get("/api/v1/services?q=nonexistent_term_xyz")
        assert resp.status_code == 200
        assert resp.json() == []
