"""
/api/v1/security — Security & Trust overview (Fase 17 §44/§45)
====================================================================
Agrega dados já expostos por outras rotas (Trust Level por módulo via
`list_modules_trust`, Publisher Registry) sob o prefixo `/security`
pedido pelo spec — nenhuma lógica de trust/publisher duplicada aqui.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.module_verification import list_modules_trust
from app.db.database import get_db
from app.module_trust.signature import SignatureStatus
from app.module_trust.trust import TrustLevel
from app.schemas.publisher import PublisherRead
from app.services.publisher import PublisherService

router = APIRouter(prefix="/security", tags=["security"])


class SecurityStatusRead(BaseModel):
    total_modules:      int
    by_trust_level:     dict[str, int]
    unsigned_count:     int
    revoked_publishers: int


@router.get("/status", response_model=SecurityStatusRead,
            summary="Aggregate security posture across all installed modules (§44)")
async def get_security_status(db: AsyncSession = Depends(get_db)) -> SecurityStatusRead:
    trust_results = await list_modules_trust(db)
    by_trust_level = {level.value: 0 for level in TrustLevel}
    unsigned_count = 0
    for result in trust_results:
        by_trust_level[result.trust_level] += 1
        if result.signature_status == SignatureStatus.NOT_CONFIGURED.value:
            unsigned_count += 1

    publishers = await PublisherService.get_all(db)
    revoked_publishers = sum(1 for p in publishers if p.trust_status == "REVOKED")

    return SecurityStatusRead(
        total_modules=len(trust_results), by_trust_level=by_trust_level,
        unsigned_count=unsigned_count, revoked_publishers=revoked_publishers,
    )


@router.get("/publishers", response_model=list[PublisherRead],
            summary="Alias of GET /publishers under the /security prefix (§45)")
async def get_security_publishers(db: AsyncSession = Depends(get_db)) -> list[PublisherRead]:
    return await PublisherService.get_all(db)
