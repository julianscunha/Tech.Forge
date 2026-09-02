"""
SDK Database Service
====================
Isolated SQLite persistence for module backends — one file per module
under modules/installed/<module_id>/data/<module_id>.db. See ADR-007.

Usage:
    from techforge_sdk import sdk
    rows = await sdk.database.fetch_all("SELECT * FROM backups WHERE active = ?", [True])
    await sdk.database.execute("INSERT INTO jobs (name) VALUES (?)", ["nightly"])
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Optional

import aiosqlite

logger = logging.getLogger("techforge.sdk.database")


class DatabaseSDK:
    """
    Isolated SQLite database for a single module.
    Each module receives its own instance, backed by its own .db file.
    """

    def __init__(self, module_id: str = "unknown", data_dir: Optional[Path] = None) -> None:
        self._module_id = module_id
        if data_dir is None:
            data_dir = Path("modules") / "installed" / module_id / "data"
        data_dir = Path(data_dir)
        data_dir.mkdir(parents=True, exist_ok=True)
        self._db_path = data_dir / f"{module_id}.db"
        self._conn: Optional[aiosqlite.Connection] = None
        self._lock: Optional[asyncio.Lock] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        # True while a caller-managed transaction (begin_transaction) is open —
        # execute()/execute_many() skip the per-call commit until commit()/rollback().
        self._in_transaction = False
        logger.debug("DatabaseSDK for module '%s' -> %s", module_id, self._db_path)

    # ── Connection ────────────────────────────────────────────────────────────

    async def _get_lock(self) -> asyncio.Lock:
        # A lock/connection created on one event loop hangs forever if reused
        # from a different, later one (e.g. a caller doing asyncio.run() per
        # call instead of one loop for the whole process — the loop the old
        # lock/connection belong to is already closed). Rebind fresh instead
        # of reusing stale state whenever the running loop has changed.
        loop = asyncio.get_running_loop()
        if self._loop is not loop:
            self._loop = loop
            self._lock = asyncio.Lock()
            self._conn = None
        return self._lock

    async def _connection(self) -> aiosqlite.Connection:
        if self._conn is None:
            self._conn = await aiosqlite.connect(self._db_path)
            self._conn.row_factory = aiosqlite.Row
        return self._conn

    # ── Query interface ───────────────────────────────────────────────────────

    async def fetch_all(
        self, query: str, params: Optional[list] = None
    ) -> list[dict[str, Any]]:
        """Execute a SELECT query and return all matching rows as dicts."""
        async with await self._get_lock():
            conn = await self._connection()
            cursor = await conn.execute(query, params or [])
            rows = await cursor.fetchall()
            await cursor.close()
            return [dict(row) for row in rows]

    async def fetch_one(
        self, query: str, params: Optional[list] = None
    ) -> Optional[dict[str, Any]]:
        """Execute a SELECT query and return the first matching row, or None."""
        rows = await self.fetch_all(query, params)
        return rows[0] if rows else None

    async def execute(self, query: str, params: Optional[list] = None) -> None:
        """Execute an INSERT, UPDATE, DELETE or DDL statement."""
        async with await self._get_lock():
            conn = await self._connection()
            await conn.execute(query, params or [])
            if not self._in_transaction:
                await conn.commit()

    async def execute_many(self, query: str, params_list: list[list[Any]]) -> None:
        """Batch execute a statement for multiple parameter sets."""
        async with await self._get_lock():
            conn = await self._connection()
            await conn.executemany(query, params_list)
            if not self._in_transaction:
                await conn.commit()

    # ── Transaction helpers ───────────────────────────────────────────────────

    async def begin_transaction(self) -> None:
        """
        Subsequent execute()/execute_many() calls won't auto-commit until commit()/rollback().

        # ponytail: doesn't hold the lock across the whole transaction, so two
        # concurrent logical transactions on the SAME DatabaseSDK instance can
        # interleave writes. Fine for the single-caller-per-module usage this
        # SDK targets today; if a module needs real concurrent transaction
        # isolation, hold the lock for the transaction's duration instead.
        """
        self._in_transaction = True

    async def commit(self) -> None:
        async with await self._get_lock():
            conn = await self._connection()
            await conn.commit()
        self._in_transaction = False

    async def rollback(self) -> None:
        async with await self._get_lock():
            conn = await self._connection()
            await conn.rollback()
        self._in_transaction = False

    async def close(self) -> None:
        """Close the underlying connection. Safe to call even if never opened."""
        if self._conn is not None:
            await self._conn.close()
            self._conn = None
