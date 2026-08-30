"""
/api/v1/services — Service Registry (Fase 8 §23)
====================================================
Majoritariamente consulta. §23 veda "execução arbitrária de serviços por
API genérica pública", mas abre exceção explícita para "necessidade
arquitetural justificada" — é o caso de /invoke abaixo: um módulo roda no
mesmo processo do Core mas o SDK nunca importa `app.*` diretamente (regra
de isolamento SDK/Core), então precisa de uma rota HTTP local pra
consumir a capacidade pública de outro módulo (dependência declarada no
manifest, Fase 8.1). Não é execução arbitrária: `invoke()` só aceita
exports já declarados no contrato público (`docs/contracts/api.yaml`) do
serviço, validados (tipo, obrigatoriedade) antes de rodar.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Body, HTTPException, Query
from pydantic import BaseModel

from app.service_registry.errors import (
    CapabilityNotFoundError,
    ContractViolationError,
    InvalidArgumentsError,
    ServiceDisabledError,
    ServiceExecutionFailedError,
    ServiceNotFoundError,
    ServiceUnavailableError,
)
from app.service_registry.invoker import invoke
from app.service_registry.registry import service_registry

router = APIRouter(prefix="/services", tags=["service-registry"])

_ERROR_STATUS = {
    ServiceNotFoundError: 404,
    CapabilityNotFoundError: 404,
    ServiceDisabledError: 503,
    ServiceUnavailableError: 503,
    ContractViolationError: 422,
    InvalidArgumentsError: 422,
    ServiceExecutionFailedError: 500,
}


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
            summary="List services, optionally filtered by keyword (§9)")
async def list_services(
    q: str | None = Query(None, description="Keyword match against service_id, "
                                              "capabilities, and export name/description"),
) -> list[ServiceDescriptorRead]:
    services = service_registry.search(q) if q else service_registry.list_services()
    return [_to_read(d) for d in services]


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


@router.post("/{service_id}/invoke/{export_name}",
             summary="Invoke a contract-declared export (§13/§23 exception — see module docstring)")
def invoke_service(
    service_id: str,
    export_name: str,
    kwargs: dict[str, Any] = Body(default_factory=dict),
) -> Any:
    # def (não async def): invoke() é síncrono e usa asyncio.run() pra
    # exports async — chamado de dentro do loop do FastAPI, isso quebraria.
    # Starlette roda handlers `def` puro numa threadpool, fora do loop.
    try:
        return invoke(service_id, export_name, **kwargs)
    except tuple(_ERROR_STATUS) as exc:
        raise HTTPException(
            _ERROR_STATUS[type(exc)], {"code": exc.code, "message": str(exc)}
        ) from None
