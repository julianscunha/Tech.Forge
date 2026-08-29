"""Module Storage API — Fase 12 §6/§7.

`context.storage` — key-value simples, isolado por module_id. O
`module_id` é fixado na construção e NUNCA é parâmetro de `get`/`set`:
um módulo não tem como ler ou escrever chave de outro módulo, mesmo por
engano de programação (isolamento estrutural, não por convenção).
"""
from __future__ import annotations

import json
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class ModuleStorageError(Exception):
    """Erro no Module Storage API — nunca vaza exceção do SQLAlchemy/json
    pro código do módulo."""


class ModuleKVStorage:
    def __init__(
        self,
        module_id: str,
        session_factory: Optional[async_sessionmaker] = None,
        session: Optional[AsyncSession] = None,
    ):
        self._module_id = module_id
        self._session_factory = session_factory
        self._session = session  # setado apenas dentro de transaction()

    def _factory(self) -> async_sessionmaker:
        if self._session_factory is not None:
            return self._session_factory
        from app.db.database import AsyncSessionLocal
        return AsyncSessionLocal

    async def get(self, key: str, default: Any = None) -> Any:
        if self._session is not None:
            return await self._get(self._session, key, default)
        async with self._factory()() as session:
            return await self._get(session, key, default)

    async def set(self, key: str, value: Any) -> None:
        try:
            value_json = json.dumps(value)
        except (TypeError, ValueError) as exc:
            raise ModuleStorageError(
                f"Valor para a chave '{key}' não é serializável em JSON: {exc}"
            ) from exc

        if self._session is not None:
            await self._set(self._session, key, value_json)
            return
        async with self._factory()() as session:
            await self._set(session, key, value_json)
            await session.commit()

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator["ModuleKVStorage"]:
        async with self._factory()() as session:
            async with session.begin():
                yield ModuleKVStorage(self._module_id, session=session)

    async def _get(self, session: AsyncSession, key: str, default: Any) -> Any:
        from app.models.module_kv_store import ModuleKVStoreRow

        row = await session.get(ModuleKVStoreRow, {"module_id": self._module_id, "key": key})
        if row is None:
            return default
        return json.loads(row.value_json)

    async def _set(self, session: AsyncSession, key: str, value_json: str) -> None:
        from app.models.module_kv_store import ModuleKVStoreRow

        row = await session.get(ModuleKVStoreRow, {"module_id": self._module_id, "key": key})
        if row is None:
            session.add(ModuleKVStoreRow(module_id=self._module_id, key=key, value_json=value_json))
        else:
            row.value_json = value_json
