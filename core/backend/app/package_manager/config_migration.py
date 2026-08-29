"""Config migration hook — Fase 12 §13/§15.

Chamado por `PackageManager.update()` antes de finalizar a nova versão.
Diferente dos hooks de lifecycle (enable/disable/health_check, Fase 9
§15 — best-effort, nunca bloqueiam a transição), uma falha aqui É um
erro de update: a spec exige "não atualizar código e deixar dados
incompatíveis silenciosamente" — o chamador (`update()`) já tem rollback
de arquivos para exceções não tratadas, reaproveitado aqui.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

import yaml

from app.module_runtime.loader import ModuleLoadError, load_module_file


class ConfigMigrationError(Exception):
    """`migrate_config()` do módulo levantou ou retornou algo inválido."""


async def run_config_migration(module_id: str, from_version: str, target_dir: Path) -> None:
    """Se o módulo (na versão NOVA, já extraída em `target_dir`) declarar
    `migrate_config(old_version, old_config) -> new_config`, chama e
    persiste o resultado. Sem efeito se o módulo não declarar o hook.

    Nunca reusa o cache de instância do `module_runtime.lifecycle` (aquele
    serve a versão ATIVA em runtime; aqui precisamos importar a versão
    NOVA recém-extraída, de um arquivo com o mesmo caminho relativo mas
    conteúdo diferente).
    """
    manifest_path = target_dir / "manifest.yaml"
    raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    entry_backend = raw.get("entry_backend")
    if not entry_backend:
        return

    backend_path = target_dir / entry_backend
    try:
        py_module = load_module_file(
            f"techforge_modules._config_migration.{module_id}", backend_path
        )
    except ModuleLoadError:
        return

    instance = getattr(py_module, "module", None)
    migrate = getattr(instance, "migrate_config", None)
    if not callable(migrate):
        return

    from app.db.database import AsyncSessionLocal
    from app.module_engine.manifest import parse_configuration_fields
    from app.services.module_configuration import ConfigValidationError, get_config, save_config

    fields = parse_configuration_fields(raw)

    async with AsyncSessionLocal() as db:
        old_config = await get_config(db, module_id, fields)
        try:
            new_config = migrate(from_version, old_config)
            if asyncio.iscoroutine(new_config):
                new_config = await new_config
            if not isinstance(new_config, dict):
                raise ConfigMigrationError(
                    f"migrate_config() de '{module_id}' retornou "
                    f"{type(new_config).__name__}, esperado dict"
                )
            await save_config(db, module_id, fields, new_config)
        except ConfigMigrationError:
            raise
        except ConfigValidationError as exc:
            raise ConfigMigrationError(
                f"migrate_config() de '{module_id}' produziu config inválida: {exc}"
            ) from exc
        except Exception as exc:
            raise ConfigMigrationError(f"migrate_config() de '{module_id}' falhou: {exc}") from exc
