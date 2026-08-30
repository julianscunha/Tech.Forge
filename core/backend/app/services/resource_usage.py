"""ResourceUsageService — Fase 14 Slice 18 (Dashboard).

CPU/memória do processo do Core via psutil (única forma razoável
multiplataforma); disco via stdlib (shutil.disk_usage). Não bloqueia o
event loop: cpu_percent(interval=None) é não-bloqueante (primeira
chamada do processo retorna 0.0 — aceitável, a Dashboard atualiza a
cada 20s de qualquer forma).
"""
from __future__ import annotations

import shutil

import psutil

from app.core.settings import settings

_process = psutil.Process()


class ResourceUsageService:

    @staticmethod
    def snapshot() -> dict:
        mem = _process.memory_info()
        disk = shutil.disk_usage(settings.BASE_DIR)
        return {
            "cpu_percent": _process.cpu_percent(interval=None),
            "memory_rss_bytes": mem.rss,
            "disk_used_bytes": disk.used,
            "disk_total_bytes": disk.total,
        }
