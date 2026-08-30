"""SupportBundleService — Fase 14 §30.

Empacota em ZIP: diagnostic snapshot, configuração da plataforma (nunca
guarda segredo — §9 da Fase 12 já garante isso, mesmo payload de
`GET /api/v1/config`), registry de módulos, grafo de dependências e os
logs recentes (já redigidos em tempo de escrita pelo SecretRedactionFilter
instalado no handler — não precisa redigir de novo aqui).

Nunca inclui: secrets, credenciais, private keys, arquivos de dados de
módulo (data/) — nenhum desses é tocado por este serviço.
"""
from __future__ import annotations

import json
import zipfile
from io import BytesIO

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.services.diagnostic_export import DiagnosticExportService

_MAX_LOG_LINES = 500


class SupportBundleService:

    @staticmethod
    async def build_zip(db: AsyncSession) -> bytes:
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            snapshot = await DiagnosticExportService.build_snapshot(db)
            zf.writestr("diagnostic_snapshot.json", DiagnosticExportService.to_json(snapshot))

            zf.writestr("platform_config.json",
                       json.dumps(settings.model_dump(mode="json"), indent=2, default=str))

            from app.module_engine.registry import registry
            modules = [
                {"module_id": e.module_id, "version": e.version, "status": e.status.value}
                for e in registry.all()
            ]
            zf.writestr("module_registry.json", json.dumps(modules, indent=2))

            from app.dependency_engine.graph import DependencyGraph
            from app.service_registry.registry import service_registry
            graph = DependencyGraph.build(registry, service_registry)
            zf.writestr("dependency_graph.mmd", graph.export_mermaid())

            log_path = settings.LOGS_PATH / "backend.jsonl"
            if log_path.exists():
                lines = log_path.read_text(encoding="utf-8").splitlines()[-_MAX_LOG_LINES:]
                zf.writestr("recent_logs.jsonl", "\n".join(lines) + ("\n" if lines else ""))

        return buffer.getvalue()
