"""Erros previsíveis do Service Registry — Fase 8 §15."""
from __future__ import annotations


class ServiceRegistryError(Exception):
    code = "SERVICE_REGISTRY_ERROR"


class ServiceNotFoundError(ServiceRegistryError):
    code = "SERVICE_NOT_FOUND"

    def __init__(self, service_id: str):
        super().__init__(f"Service not found: {service_id!r}")
        self.service_id = service_id


class CapabilityNotFoundError(ServiceRegistryError):
    code = "CAPABILITY_NOT_FOUND"

    def __init__(self, capability: str):
        super().__init__(f"Capability not found: {capability!r}")
        self.capability = capability


class ServiceDisabledError(ServiceRegistryError):
    code = "SERVICE_DISABLED"

    def __init__(self, service_id: str):
        super().__init__(f"Service is disabled: {service_id!r}")
        self.service_id = service_id


class ServiceUnavailableError(ServiceRegistryError):
    code = "SERVICE_UNAVAILABLE"

    def __init__(self, service_id: str):
        super().__init__(f"Service is unavailable: {service_id!r}")
        self.service_id = service_id


class ContractViolationError(ServiceRegistryError):
    code = "CONTRACT_VIOLATION"


class InvalidArgumentsError(ServiceRegistryError):
    code = "INVALID_ARGUMENTS"


class ServiceExecutionFailedError(ServiceRegistryError):
    code = "SERVICE_EXECUTION_FAILED"
