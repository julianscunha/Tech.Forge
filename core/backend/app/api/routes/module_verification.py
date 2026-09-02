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
from app.module_trust.service import get_module_trust_result, list_all_module_trust
from app.module_trust.verification import verify_module_integrity
from app.schemas.publisher import PublisherRead

router = APIRouter(prefix="/modules", tags=["module-trust"])


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
    return [TrustRead(**r.__dict__) for r in await list_all_module_trust(registry, db)]


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
    result = await get_module_trust_result(module_id, package_dir, entry.manifest_raw or {}, db)
    return TrustRead(**result.__dict__)


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
    Publisher (`get_module_trust_result`) — nenhuma lógica de resolução duplicada."""
    entry = registry.get(module_id)
    if entry is None:
        raise HTTPException(404, f"Module not found: {module_id!r}")

    package_dir = settings.MODULES_INSTALLED_PATH / module_id
    raw = entry.manifest_raw or {}
    trust = await get_module_trust_result(module_id, package_dir, raw, db)
    dependencies = DependencyParser.parse(raw.get("dependencies") or [])

    return SBOMRead(
        module=module_id, version=entry.version,
        dependencies=[SBOMDependencyRead(
            target_type=d.target_type.value, target_id=d.target_id,
            version_range=d.version_range, required=d.required) for d in dependencies],
        publisher=trust.publisher, checksum=raw.get("checksum"),
        signature_status=trust.signature_status,
    )
