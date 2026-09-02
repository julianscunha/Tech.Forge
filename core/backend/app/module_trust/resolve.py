"""
Shared Trust resolution core — used by both the on-demand
GET /modules/{id}/trust API and the install()/update() pipeline (TD-005).
"""
from __future__ import annotations

import base64
from pathlib import Path
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.module_trust.integrity import IntegrityStatus, verify_integrity
from app.module_trust.signature import canonical_manifest_bytes, default_signature_provider
from app.module_trust.trust import TrustLevel, TrustResolver
from app.services.publisher import PublisherService


async def resolve_module_trust(
    target_dir: Path, raw_manifest: dict, db: AsyncSession,
) -> tuple[TrustLevel, IntegrityStatus, str, Optional[object]]:
    """
    Resolve a module's TrustLevel from its on-disk integrity state, manifest
    signature, and a DB publisher lookup.

    Returns (trust_level, integrity_status, signature_status, publisher).
    """
    integrity_result = verify_integrity(target_dir)

    publisher_field = raw_manifest.get("publisher")
    publisher_id = (publisher_field.get("id")
                    if isinstance(publisher_field, dict) else publisher_field)
    publisher = await PublisherService.get_by_id(db, publisher_id) if publisher_id else None

    signature_value = raw_manifest.get("signature")
    signature_bytes = base64.b64decode(signature_value) if signature_value else None
    signature_status = default_signature_provider.verify(
        data=canonical_manifest_bytes(raw_manifest), signature=signature_bytes,
        public_key=publisher.public_key if publisher else None,
    ).value

    trust_level = TrustResolver.resolve(integrity_result.status, publisher, signature_status)
    return trust_level, integrity_result.status, signature_status, publisher
