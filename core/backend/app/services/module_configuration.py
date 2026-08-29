"""Module configuration — validação tipada + persistência (Fase 12 §10/§12).

Schema dinâmico via pydantic.create_model sobre os campos declarados no
manifest do módulo. Config inválida nunca chega a persistir.
"""
from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError, create_model
from sqlalchemy.ext.asyncio import AsyncSession

from app.module_engine.manifest import ConfigField

_TYPE_MAP: dict[str, type] = {
    "string": str,
    "integer": int,
    "float": float,
    "boolean": bool,
}


class ConfigValidationError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


def _build_schema(fields: list[ConfigField]):
    schema_fields: dict[str, Any] = {}
    for f in fields:
        py_type = _TYPE_MAP[f.type]
        default = ... if f.default is None else f.default
        schema_fields[f.id] = (py_type, default)
    return create_model("ModuleConfigSchema", **schema_fields)


def validate_config(fields: list[ConfigField], values: dict[str, Any]) -> dict[str, Any]:
    if not fields:
        if values:
            raise ConfigValidationError(["Este módulo não declara nenhum campo de configuração."])
        return {}

    known_ids = {f.id for f in fields}
    unknown = set(values) - known_ids
    if unknown:
        raise ConfigValidationError([f"Campo(s) desconhecido(s): {', '.join(sorted(unknown))}"])

    schema = _build_schema(fields)
    try:
        instance = schema(**values)
    except ValidationError as exc:
        raise ConfigValidationError(
            [f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors()]
        ) from exc
    return instance.model_dump()


async def get_config(db: AsyncSession, module_id: str, fields: list[ConfigField]) -> dict[str, Any]:
    from app.models.module_configuration import ModuleConfiguration

    row = await db.get(ModuleConfiguration, module_id)
    if row is None:
        return validate_config(fields, {})
    return json.loads(row.values_json)


async def save_config(
    db: AsyncSession, module_id: str, fields: list[ConfigField], values: dict[str, Any]
) -> dict[str, Any]:
    from app.models.module_configuration import ModuleConfiguration

    validated = validate_config(fields, values)  # levanta antes de tocar o banco

    row = await db.get(ModuleConfiguration, module_id)
    if row is None:
        row = ModuleConfiguration(module_id=module_id, values_json=json.dumps(validated))
        db.add(row)
    else:
        row.values_json = json.dumps(validated)
    await db.commit()
    return validated
