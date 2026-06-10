"""
SDK Database Service
====================
Provides isolated database access for module backends.

Phase 3: in-memory mock that validates query structure and returns
         typed results. Modules can develop and test without a live DB.
Phase 4: replaced by a real AsyncSession scoped to the module's schema.

Usage:
    from techforge_sdk import sdk
    rows = await sdk.database.fetch_all("SELECT * FROM backups WHERE active = ?", [True])
    await sdk.database.execute("INSERT INTO jobs (name) VALUES (?)", ["nightly"])
"""
from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger("techforge.sdk.database")


class DatabaseSDK:
    """
    Isolated database access for a single module.
    Each module receives its own instance scoped to its module_id.
    """

    def __init__(self, module_id: str = "unknown") -> None:
        self._module_id = module_id
        self._mock_store: dict[str, list[dict]] = {}
        logger.debug("DatabaseSDK initialised for module '%s'", module_id)

    # ── Query interface ───────────────────────────────────────────────────────

    async def fetch_all(
        self, query: str, params: Optional[list] = None
    ) -> list[dict[str, Any]]:
        """
        Execute a SELECT query and return all matching rows.

        Phase 3 mock: returns rows stored via execute() for the same table.
        Phase 4: executes against the real SQLite/PostgreSQL session.

        Args:
            query:  Raw SQL string. Use ? for positional parameters.
            params: Positional parameter values.

        Returns:
            List of row dicts. Empty list if no rows found.
        """
        logger.debug("[%s] fetch_all: %s | params=%s", self._module_id, query[:60], params)
        table = self._extract_table(query)
        return self._mock_store.get(table, [])

    async def fetch_one(
        self, query: str, params: Optional[list] = None
    ) -> Optional[dict[str, Any]]:
        """
        Execute a SELECT query and return the first matching row, or None.
        """
        rows = await self.fetch_all(query, params)
        return rows[0] if rows else None

    async def execute(
        self, query: str, params: Optional[list] = None
    ) -> None:
        """
        Execute an INSERT, UPDATE, or DELETE statement.

        Phase 3 mock: stores rows in the in-memory mock store for
        subsequent fetch_all() calls within the same process.
        """
        logger.debug("[%s] execute: %s | params=%s", self._module_id, query[:60], params)
        if query.strip().upper().startswith("INSERT") and params:
            table = self._extract_table(query)
            if table not in self._mock_store:
                self._mock_store[table] = []
            self._mock_store[table].append({"_params": params})

    async def execute_many(
        self, query: str, params_list: list[list[Any]]
    ) -> None:
        """Batch execute a statement for multiple parameter sets."""
        for params in params_list:
            await self.execute(query, params)

    # ── Transaction helpers ───────────────────────────────────────────────────

    async def begin_transaction(self) -> None:
        """Phase 4: wraps subsequent calls in an atomic transaction."""
        logger.debug("[%s] begin_transaction (mock no-op)", self._module_id)

    async def commit(self) -> None:
        """Phase 4: commits the current transaction."""
        logger.debug("[%s] commit (mock no-op)", self._module_id)

    async def rollback(self) -> None:
        """Phase 4: rolls back the current transaction."""
        logger.debug("[%s] rollback (mock no-op)", self._module_id)

    # ── Internal ──────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_table(query: str) -> str:
        """Best-effort table name extraction for mock routing."""
        tokens = query.upper().split()
        for kw in ("FROM", "INTO", "UPDATE", "TABLE"):
            if kw in tokens:
                idx = tokens.index(kw)
                if idx + 1 < len(tokens):
                    return tokens[idx + 1].strip("(),;").lower()
        return "_default"
