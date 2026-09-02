"""
DatabaseSDK — persistence, isolation, and transaction tests (ADR-007).
"""
import pytest

from techforge_sdk.database import DatabaseSDK


@pytest.mark.asyncio
async def test_persists_across_instances(tmp_path):
    db1 = DatabaseSDK("mod_a", tmp_path)
    await db1.execute("CREATE TABLE jobs (name TEXT)")
    await db1.execute("INSERT INTO jobs (name) VALUES (?)", ["nightly"])
    await db1.close()

    db2 = DatabaseSDK("mod_a", tmp_path)
    rows = await db2.fetch_all("SELECT * FROM jobs")
    assert rows == [{"name": "nightly"}]


@pytest.mark.asyncio
async def test_modules_are_isolated(tmp_path):
    db_a = DatabaseSDK("mod_a", tmp_path / "mod_a")
    db_b = DatabaseSDK("mod_b", tmp_path / "mod_b")
    await db_a.execute("CREATE TABLE t (v INT)")
    await db_a.execute("INSERT INTO t VALUES (1)")

    with pytest.raises(Exception):
        await db_b.fetch_all("SELECT * FROM t")


@pytest.mark.asyncio
async def test_rollback_discards_uncommitted_writes(tmp_path):
    db = DatabaseSDK("mod_c", tmp_path)
    await db.execute("CREATE TABLE t (v INT)")

    await db.begin_transaction()
    await db.execute("INSERT INTO t VALUES (1)")
    await db.rollback()

    rows = await db.fetch_all("SELECT * FROM t")
    assert rows == []


@pytest.mark.asyncio
async def test_commit_persists_transaction(tmp_path):
    db = DatabaseSDK("mod_d", tmp_path)
    await db.execute("CREATE TABLE t (v INT)")

    await db.begin_transaction()
    await db.execute("INSERT INTO t VALUES (1)")
    await db.execute("INSERT INTO t VALUES (2)")
    await db.commit()

    rows = await db.fetch_all("SELECT * FROM t")
    assert rows == [{"v": 1}, {"v": 2}]


@pytest.mark.asyncio
async def test_fetch_one_returns_none_when_empty(tmp_path):
    db = DatabaseSDK("mod_e", tmp_path)
    await db.execute("CREATE TABLE t (v INT)")
    assert await db.fetch_one("SELECT * FROM t") is None
