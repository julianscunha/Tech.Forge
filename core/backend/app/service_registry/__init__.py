"""
Service Registry — Fase 8
===========================
Descoberta e registro de capacidades de Service Modules. Paralelo ao
`module_engine/registry.py`: in-memory, singleton, reconstruível no boot a
partir dos módulos instalados (§25) — nenhuma persistência em banco nesta
fase.
"""
from app.service_registry.descriptor import ServiceDescriptor, ServiceStatus
from app.service_registry.registry import ServiceRegistry, service_registry, sync
from app.service_registry.invoker import invoke

__all__ = [
    "ServiceDescriptor", "ServiceStatus", "ServiceRegistry", "service_registry",
    "sync", "invoke",
]
