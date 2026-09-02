"""
Module Trust — orchestration service (TD-002).

Resolves a module's Trust Level and fires the associated security events
(signature_valid/invalid, module_trust_changed). Shared by every consumer
that needs this — routes call this, never each other, so a route is never
treated as if it were a service layer.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.module_engine.enums import ModuleStatus
from app.module_trust.resolve import resolve_module_trust
from app.module_trust.signature import SignatureStatus
from app.observability.events import event_bus

# Fase 17 §36 — cache in-memory do último Trust Level resolvido por módulo,
# só pra detectar transição real (MODULE_TRUST_CHANGED). Não persiste entre
# restarts — o Trust Level em si sempre é recalculado do zero a cada chamada.
_last_known_trust: dict[str, str] = {}


@dataclass
class ModuleTrustResult:
    module_id:         str
    trust_level:       str
    integrity_status:  str
    signature_status:  str
    publisher:         Optional[object]


async def get_module_trust_result(
    module_id: str, package_dir: Path, raw_manifest: dict, db: AsyncSession,
) -> ModuleTrustResult:
    """Resolve one module's Trust Level and fire security events on change."""
    trust_level, integrity_status, signature_status, publisher = await resolve_module_trust(
        package_dir, raw_manifest, db)

    if signature_status == SignatureStatus.VALID.value:
        event_bus.publish("security.signature_valid", module_id=module_id)
    elif signature_status == SignatureStatus.INVALID.value:
        event_bus.publish("security.signature_invalid", module_id=module_id)

    previous = _last_known_trust.get(module_id)
    if previous is not None and previous != trust_level.value:
        event_bus.publish("security.module_trust_changed", module_id=module_id,
                          **{"from": previous, "to": trust_level.value})
    _last_known_trust[module_id] = trust_level.value

    return ModuleTrustResult(
        module_id=module_id, trust_level=trust_level.value,
        integrity_status=integrity_status.value, signature_status=signature_status,
        publisher=publisher,
    )


async def list_all_module_trust(registry, db: AsyncSession) -> list[ModuleTrustResult]:
    """Trust Level of every INSTALLED module (§21/§22 — avoid N+1 from callers)."""
    results: list[ModuleTrustResult] = []
    for entry in registry.all():
        if entry.status != ModuleStatus.INSTALLED:
            continue
        package_dir = settings.MODULES_INSTALLED_PATH / entry.module_id
        results.append(await get_module_trust_result(
            entry.module_id, package_dir, entry.manifest_raw or {}, db))
    return results
