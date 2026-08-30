"""
ServiceDescriptor — Fase 8 §8/§11
====================================
Separa module state (INSTALLED/DISABLED/...) de service availability:
um módulo pode estar ativo enquanto um serviço específico está indisponível
(falha de inicialização, conflito de capability, etc).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Optional

from app.doc_engine.models import ServiceContract


class ServiceStatus(str, Enum):
    REGISTERED  = "REGISTERED"
    ACTIVE      = "ACTIVE"
    UNAVAILABLE = "UNAVAILABLE"
    DISABLED    = "DISABLED"
    FAILED      = "FAILED"
    REMOVED     = "REMOVED"


@dataclass
class ServiceDescriptor:
    """
    Modelo interno do Service Registry (§11) — serializável e independente
    da implementação do serviço.
    """
    service_id:      str
    module_id:       str
    module_version:  str
    service_version: str
    capabilities:    list[str] = field(default_factory=list)
    contract:        Optional[ServiceContract] = None
    status:          ServiceStatus = ServiceStatus.REGISTERED
    metadata:        dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "service_id":      self.service_id,
            "module_id":       self.module_id,
            "module_version":  self.module_version,
            "service_version": self.service_version,
            "capabilities":    list(self.capabilities),
            "contract":        asdict(self.contract) if self.contract else None,
            "status":          self.status.value,
            "metadata":        dict(self.metadata),
        }
