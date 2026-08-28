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
from app.module_engine.registry import registry
from app.module_trust.integrity import verify_integrity
from app.module_trust.signature import default_signature_provider
from app.module_trust.trust import TrustResolver
from app.module_trust.verification import verify_module_integrity
from app.schemas.publisher import PublisherRead
from app.services.publisher import PublisherService

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
    integrity_result = verify_integrity(package_dir)

    raw = entry.manifest_raw or {}
    publisher_field = raw.get("publisher")
    publisher_id = (publisher_field.get("id")
                    if isinstance(publisher_field, dict) else publisher_field)
    publisher = await PublisherService.get_by_id(db, publisher_id) if publisher_id else None

    signature_value = raw.get("signature")
    signature_status = default_signature_provider.verify(
        data=b"", signature=signature_value.encode() if signature_value else None,
        public_key=publisher.public_key if publisher else None,
    ).value

    trust_level = TrustResolver.resolve(integrity_result.status, publisher, signature_status)

    return TrustRead(
        module_id=module_id, trust_level=trust_level.value,
        integrity_status=integrity_result.status.value, signature_status=signature_status,
        publisher=publisher,
    )
