"""
POST /api/v1/modules/{id}/verify — Runtime Integrity Verification
=====================================================================
Fase 10 §15/§20/§26 — reverifica integridade sob demanda. Não é
polling: chamado manualmente, no startup, ou depois de update.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.db.database import get_db
from app.dependency_engine.parser import DependencyParser
from app.module_engine.registry import registry
from app.module_trust.integrity import verify_integrity
from app.module_trust.resolve import resolve_module_trust
from app.module_trust.signature import SignatureStatus
from app.module_trust.verification import verify_module_integrity
from app.observability.events import event_bus
from app.schemas.publisher import PublisherRead
from app.services.publisher import PublisherService

router = APIRouter(prefix="/modules", tags=["module-trust"])

# Fase 17 §36 — cache in-memory do último Trust Level resolvido por
# módulo, só pra detectar transição real (MODULE_TRUST_CHANGED). Não
# persiste entre restarts — decisão consciente, o Trust Level em si
# sempre é recalculado do zero a cada chamada, isto é só pra saber se
# mudou desde a última verificação nesta sessão do processo.
_last_known_trust: dict[str, str] = {}


class IntegrityVerifyRead(BaseModel):
    module_id:         str
    status:            str
    modified_files:    list[str]
    missing_files:     list[str]
    unexpected_files:  list[str]


class TrustRead(BaseModel):
    module_id:         str
    trust_level:       str
    integrity_status:  str
    signature_status:  str
    publisher:         Optional[PublisherRead] = None


@router.post("/{module_id}/verify", response_model=IntegrityVerifyRead,
             summary="Reverify a module's integrity on demand (§15/§20)")
async def verify_module(module_id: str, db: AsyncSession = Depends(get_db)) -> IntegrityVerifyRead:
    if registry.get(module_id) is None:
        raise HTTPException(404, f"Module not found: {module_id!r}")

    result = await verify_module_integrity(module_id, db)
    return IntegrityVerifyRead(
        module_id=module_id, status=result.status.value,
        modified_files=result.modified_files, missing_files=result.missing_files,
        unexpected_files=result.unexpected_files,
    )


@router.get("/trust", response_model=list[TrustRead],
            summary="Trust Level of every INSTALLED module in one call (§21/§22 — avoid N+1)")
async def list_modules_trust(db: AsyncSession = Depends(get_db)) -> list[TrustRead]:
    from app.module_engine.enums import ModuleStatus

    results: list[TrustRead] = []
    for entry in registry.all():
        if entry.status != ModuleStatus.INSTALLED:
            continue
        results.append(await get_module_trust(entry.module_id, db))
    return results


@router.get("/{module_id}/integrity", response_model=IntegrityVerifyRead,
            summary="Read a module's current integrity status (§24, GET — no side effects)")
async def get_module_integrity(module_id: str) -> IntegrityVerifyRead:
    if registry.get(module_id) is None:
        raise HTTPException(404, f"Module not found: {module_id!r}")

    package_dir = settings.MODULES_INSTALLED_PATH / module_id
    result = verify_integrity(package_dir)
    return IntegrityVerifyRead(
        module_id=module_id, status=result.status.value,
        modified_files=result.modified_files, missing_files=result.missing_files,
        unexpected_files=result.unexpected_files,
    )


@router.get("/{module_id}/trust", response_model=TrustRead,
            summary="Full Trust Level resolution with real Publisher lookup (§8/§24)")
async def get_module_trust(module_id: str, db: AsyncSession = Depends(get_db)) -> TrustRead:
    entry = registry.get(module_id)
    if entry is None:
        raise HTTPException(404, f"Module not found: {module_id!r}")

    package_dir = settings.MODULES_INSTALLED_PATH / module_id
    raw = entry.manifest_raw or {}
    trust_level, integrity_status, signature_status, publisher = await resolve_module_trust(package_dir, raw, db)

    if signature_status == SignatureStatus.VALID.value:
        event_bus.publish("security.signature_valid", module_id=module_id)
    elif signature_status == SignatureStatus.INVALID.value:
        event_bus.publish("security.signature_invalid", module_id=module_id)

    previous = _last_known_trust.get(module_id)
    if previous is not None and previous != trust_level.value:
        event_bus.publish("security.module_trust_changed", module_id=module_id,
                          **{"from": previous, "to": trust_level.value})
    _last_known_trust[module_id] = trust_level.value

    return TrustRead(
        module_id=module_id, trust_level=trust_level.value,
        integrity_status=integrity_status.value, signature_status=signature_status,
        publisher=publisher,
    )


class SBOMDependencyRead(BaseModel):
    target_type:   str
    target_id:     str
    version_range: Optional[str] = None
    required:      bool


class SBOMRead(BaseModel):
    module:           str
    version:          str
    dependencies:     list[SBOMDependencyRead]
    publisher:        Optional[PublisherRead] = None
    checksum:         Optional[str] = None
    signature_status: str


@router.get("/{module_id}/sbom", response_model=SBOMRead,
            summary="Minimal Software Bill of Materials (§31/§32) — no SPDX/CycloneDX")
async def get_module_sbom(module_id: str, db: AsyncSession = Depends(get_db)) -> SBOMRead:
    """Reaproveita dependency_engine (dependências já declaradas) + Trust/
    Publisher (`get_module_trust`) — nenhuma lógica de resolução duplicada."""
    entry = registry.get(module_id)
    if entry is None:
        raise HTTPException(404, f"Module not found: {module_id!r}")

    trust = await get_module_trust(module_id, db)
    raw = entry.manifest_raw or {}
    dependencies = DependencyParser.parse(raw.get("dependencies") or [])

    return SBOMRead(
        module=module_id, version=entry.version,
        dependencies=[SBOMDependencyRead(
            target_type=d.target_type.value, target_id=d.target_id,
            version_range=d.version_range, required=d.required) for d in dependencies],
        publisher=trust.publisher, checksum=raw.get("checksum"),
        signature_status=trust.signature_status,
    )
