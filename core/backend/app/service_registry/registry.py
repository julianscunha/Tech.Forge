"""
ServiceRegistry — Fase 8 §2/§7/§9/§17/§25/§26/§27
=====================================================
In-memory, singleton, reconstruível a partir do ModuleRegistry — mesmo
padrão da fonte única de verdade já documentada em docs/architecture.md.
Nenhuma persistência em banco nesta fase (§25): `rebuild()` é chamado após
qualquer mutação do ModuleRegistry (boot, activate/deactivate, remove).
"""
from __future__ import annotations

from typing import Iterable

from app.module_engine.enums import ModuleStatus
from app.service_registry.descriptor import ServiceDescriptor, ServiceStatus


class ServiceRegistry:
    """
    Usage:
        service_registry.rebuild(module_registry.all(), doc_indexer)
        service_registry.find_service("aws.costs")
    """

    def __init__(self) -> None:
        self._services: dict[str, ServiceDescriptor] = {}

    # ── Rebuild (§25/§26) ───────────────────────────────────────────────────

    def rebuild(self, module_entries: Iterable, doc_indexer) -> None:
        """
        Discover Service Modules → Register Services (§26). Only modules
        with module_type == "service" and status INSTALLED/DISABLED become
        service descriptors — a module without a valid contract is still
        registered, but as FAILED (§26: a falha de um serviço não deve
        derrubar o Core nem impedir os demais de registrar).
        """
        services: dict[str, ServiceDescriptor] = {}
        for entry in module_entries:
            if getattr(entry, "module_type", "application") != "service":
                continue
            if entry.status not in (ModuleStatus.INSTALLED, ModuleStatus.DISABLED):
                continue

            contract = doc_indexer.get_contract(entry.module_id)
            if contract is None:
                descriptor = ServiceDescriptor(
                    service_id=entry.module_id, module_id=entry.module_id,
                    module_version=entry.version, service_version="0.0.0",
                    status=ServiceStatus.FAILED,
                    metadata={"error": "no valid docs/contracts/api.yaml found"},
                )
            else:
                status = (ServiceStatus.ACTIVE if entry.status == ModuleStatus.INSTALLED
                          else ServiceStatus.DISABLED)
                descriptor = ServiceDescriptor(
                    service_id=contract.service_id, module_id=entry.module_id,
                    module_version=entry.version, service_version=contract.version,
                    capabilities=list(contract.capabilities), contract=contract,
                    status=status,
                )
            services[descriptor.service_id] = descriptor

        self._services = services

    def clear_transient_state(self) -> None:
        """§27 — shutdown clears in-memory state, never installation metadata."""
        self._services = {}

    # ── Discovery (§9) ───────────────────────────────────────────────────────

    def find_service(self, service_id: str) -> ServiceDescriptor | None:
        return self._services.get(service_id)

    def find_by_module(self, module_id: str) -> ServiceDescriptor | None:
        return next((d for d in self._services.values() if d.module_id == module_id), None)

    def list_services(self) -> list[ServiceDescriptor]:
        return list(self._services.values())

    def find_capability(self, capability: str) -> list[ServiceDescriptor]:
        return [d for d in self._services.values() if capability in d.capabilities]

    def list_capabilities(self) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        for d in self._services.values():
            for cap in d.capabilities:
                out.setdefault(cap, []).append(d.service_id)
        return out

    # ── Conflicts (§17) ──────────────────────────────────────────────────────

    def list_conflicts(self) -> dict[str, list[str]]:
        """Capabilities provided by more than one ACTIVE service."""
        active_caps: dict[str, list[str]] = {}
        for d in self._services.values():
            if d.status != ServiceStatus.ACTIVE:
                continue
            for cap in d.capabilities:
                active_caps.setdefault(cap, []).append(d.service_id)
        return {cap: providers for cap, providers in active_caps.items() if len(providers) > 1}


service_registry = ServiceRegistry()


def sync() -> None:
    """Rebuild the Service Registry from the current ModuleRegistry state."""
    from app.module_engine.registry import registry as module_registry
    from app.doc_engine import doc_indexer

    service_registry.rebuild(module_registry.all(), doc_indexer)
