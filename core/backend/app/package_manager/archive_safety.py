"""Resource limits na extração de pacotes — Fase 17 §16/§18.

Threat model: Denial of Service (zip bomb) — um .mod de poucos KB pode
declarar gigabytes de conteúdo descomprimido ou dezenas de milhares de
arquivos e travar a instalação. Checagem via `ZipFile.infolist()` (que
lê só o índice central, nunca descomprime nada) ANTES de extrair
qualquer membro — nada toca disco se o pacote exceder os limites.

`zipfile.extract()` do stdlib (desde Python 3.6.4) já sanitiza path
traversal (`..`, paths absolutos, drive letters) — não duplicado aqui.
"""
from __future__ import annotations

import zipfile
from pathlib import Path

from app.core.settings import settings
from app.observability.events import event_bus


class PackageTooLargeError(Exception):
    """Pacote excede os limites de tamanho descomprimido ou contagem de arquivos."""


def safe_extract(zf: zipfile.ZipFile, dest: Path, skip_prefix: str | None = None,
                 module_id: str | None = None) -> None:
    members = [
        m for m in zf.infolist()
        if not (skip_prefix and m.filename.startswith(skip_prefix))
    ]

    if len(members) > settings.MAX_PACKAGE_FILE_COUNT:
        reason = (f"Package has {len(members)} files, exceeds limit of "
                 f"{settings.MAX_PACKAGE_FILE_COUNT}")
        event_bus.publish("security.module_blocked", module_id=module_id, reason=reason)
        raise PackageTooLargeError(reason)

    total_size = sum(m.file_size for m in members)
    if total_size > settings.MAX_PACKAGE_UNCOMPRESSED_SIZE:
        reason = (f"Package uncompressed size {total_size} bytes exceeds limit of "
                 f"{settings.MAX_PACKAGE_UNCOMPRESSED_SIZE} bytes")
        event_bus.publish("security.module_blocked", module_id=module_id, reason=reason)
        raise PackageTooLargeError(reason)

    for member in members:
        zf.extract(member, dest)
