import logging

import aiosqlite

from backend.app.config import get_settings
from backend.app.database.migrations import SCHEMA_SQL

logger = logging.getLogger("societas.database")

_connection: aiosqlite.Connection | None = None


async def get_connection() -> aiosqlite.Connection:
    global _connection
    if _connection is None:
        db_path = get_settings().database_path
        _connection = await aiosqlite.connect(db_path)
        _connection.row_factory = aiosqlite.Row
        await _connection.execute("PRAGMA journal_mode=WAL;")
        logger.info("Database connection opened: %s", db_path)
    return _connection


async def init_db() -> None:
    conn = await get_connection()
    for statement in SCHEMA_SQL.strip().split(";"):
        stmt = statement.strip()
        if stmt:
            await conn.execute(stmt)
    await conn.commit()
    logger.info("Database schema initialized")


async def close_db() -> None:
    global _connection
    if _connection is not None:
        await _connection.close()
        _connection = None
        logger.info("Database connection closed")
