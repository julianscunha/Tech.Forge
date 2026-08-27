"""
/api/v1/services — Service Registry (Fase 8 §23)
====================================================
Somente consulta — nenhuma rota genérica de invocação pública (§23: não
permitir execução arbitrária de serviços por API genérica).
"""
from __future__ import annotations

from dataclasses import asdict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.service_registry.registry import service_registry

router = APIRouter(prefix="/services", tags=["service-registry"])


class ServiceExportRead(BaseModel):
    name: str
    description: str
    parameters: list[dict]
    returns: str | None
    examples: list[str]


class ServiceContractRead(BaseModel):
    service_id: str
    module_id: str
    description: str
    version: str
    exports: list[ServiceExportRead]
    dependencies: list[str]
    capabilities: list[str]


class ServiceDescriptorRead(BaseModel):
    service_id: str
    module_id: str
    module_version: str
    service_version: str
    capabilities: list[str]
    status: str
    contract: ServiceContractRead | None


def _to_read(descriptor) -> ServiceDescriptorRead:
    data = descriptor.to_dict()
    return ServiceDescriptorRead(**data)


@router.get("", response_model=list[ServiceDescriptorRead],
            summary="List all registered services (§9)")
async def list_services() -> list[ServiceDescriptorRead]:
    return [_to_read(d) for d in service_registry.list_services()]


@router.get("/capabilities", response_model=dict[str, list[str]],
            summary="Map every discovered capability to its providing service_id(s) (§9/§17)")
async def list_capabilities() -> dict[str, list[str]]:
    return service_registry.list_capabilities()


@router.get("/capabilities/{capability}", response_model=list[ServiceDescriptorRead],
            summary="Find which service(s) provide a capability (§9)")
async def get_capability(capability: str) -> list[ServiceDescriptorRead]:
    return [_to_read(d) for d in service_registry.find_capability(capability)]


@router.get("/{service_id}", response_model=ServiceDescriptorRead,
            summary="Get one service descriptor (§9)")
async def get_service(service_id: str) -> ServiceDescriptorRead:
    descriptor = service_registry.find_service(service_id)
    if descriptor is None:
        raise HTTPException(404, f"Service not found: {service_id!r}")
    return _to_read(descriptor)


@router.get("/{service_id}/contract", response_model=ServiceContractRead,
            summary="Get a service's public contract (§10)")
async def get_service_contract(service_id: str) -> ServiceContractRead:
    descriptor = service_registry.find_service(service_id)
    if descriptor is None or descriptor.contract is None:
        raise HTTPException(404, f"Contract not found for service: {service_id!r}")
    return ServiceContractRead(**asdict(descriptor.contract))
