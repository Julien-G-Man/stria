from __future__ import annotations

import json
import logging
import os
from typing import Any

from stria.config import get_settings
from stria.models import ReadResponse

logger = logging.getLogger(__name__)

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS scan_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL UNIQUE,
    timestamp TEXT NOT NULL,
    cassette_type TEXT NOT NULL,
    outcome TEXT NOT NULL,
    confidence REAL NOT NULL,
    payload_json TEXT NOT NULL
);
"""

_INSERT_SQL = """
INSERT OR IGNORE INTO scan_results
    (request_id, timestamp, cassette_type, outcome, confidence, payload_json)
VALUES (?, ?, ?, ?, ?, ?);
"""

_SELECT_RECENT_SQL = """
SELECT payload_json FROM scan_results
ORDER BY id DESC LIMIT ?;
"""


# ---------------------------------------------------------------------------
# Backend detection
# ---------------------------------------------------------------------------

def _use_postgres() -> bool:
    return bool(get_settings().database_url)


# ---------------------------------------------------------------------------
# SQLite (local)
# ---------------------------------------------------------------------------

async def _sqlite_init() -> None:
    import aiosqlite
    settings = get_settings()
    db_path = settings.sqlite_db_path
    os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
    async with aiosqlite.connect(db_path) as db:
        await db.execute(_CREATE_TABLE_SQL)
        await db.commit()


async def _sqlite_save(response: ReadResponse) -> None:
    import aiosqlite
    settings = get_settings()
    payload = response.model_dump_json()
    async with aiosqlite.connect(settings.sqlite_db_path) as db:
        await db.execute(
            _INSERT_SQL,
            (
                response.request_id,
                response.timestamp,
                response.cassette_type.value,
                response.result.outcome,
                response.result.confidence,
                payload,
            ),
        )
        await db.commit()


async def _sqlite_get_history(limit: int) -> list[ReadResponse]:
    import aiosqlite
    settings = get_settings()
    results = []
    async with aiosqlite.connect(settings.sqlite_db_path) as db:
        async with db.execute(_SELECT_RECENT_SQL, (limit,)) as cursor:
            rows = await cursor.fetchall()
    for row in rows:
        try:
            results.append(ReadResponse.model_validate_json(row[0]))
        except Exception as exc:
            logger.warning("Failed to deserialise scan result: %s", exc)
    return results


# ---------------------------------------------------------------------------
# Postgres (production)
# ---------------------------------------------------------------------------

_pg_pool: Any = None


async def _postgres_init() -> None:
    global _pg_pool
    import asyncpg
    settings = get_settings()
    _pg_pool = await asyncpg.create_pool(settings.database_url, min_size=1, max_size=5)
    async with _pg_pool.acquire() as conn:
        await conn.execute(
            _CREATE_TABLE_SQL.replace(
                "INTEGER PRIMARY KEY AUTOINCREMENT",
                "SERIAL PRIMARY KEY",
            ).replace(
                "INSERT OR IGNORE",
                "INSERT",
            )
        )


async def _postgres_save(response: ReadResponse) -> None:
    payload = response.model_dump_json()
    async with _pg_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO scan_results
                (request_id, timestamp, cassette_type, outcome, confidence, payload_json)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (request_id) DO NOTHING
            """,
            response.request_id,
            response.timestamp,
            response.cassette_type.value,
            response.result.outcome,
            response.result.confidence,
            payload,
        )


async def _postgres_get_history(limit: int) -> list[ReadResponse]:
    results = []
    async with _pg_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT payload_json FROM scan_results ORDER BY id DESC LIMIT $1", limit
        )
    for row in rows:
        try:
            results.append(ReadResponse.model_validate_json(row["payload_json"]))
        except Exception as exc:
            logger.warning("Failed to deserialise scan result: %s", exc)
    return results


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def init() -> None:
    """Create tables. Call during FastAPI lifespan startup."""
    if _use_postgres():
        await _postgres_init()
    else:
        await _sqlite_init()
    logger.info("Storage backend initialised (%s)", "postgres" if _use_postgres() else "sqlite")


async def save_result(response: ReadResponse) -> None:
    """Persist a scan result. Swallows exceptions — never blocks the HTTP response."""
    try:
        if _use_postgres():
            await _postgres_save(response)
        else:
            await _sqlite_save(response)
    except Exception as exc:
        logger.error("Failed to save scan result %s: %s", response.request_id, exc)


async def get_history(limit: int = 20) -> list[ReadResponse]:
    """Return the most recent scan results, newest first."""
    try:
        if _use_postgres():
            return await _postgres_get_history(limit)
        return await _sqlite_get_history(limit)
    except Exception as exc:
        logger.error("Failed to fetch history: %s", exc)
        return []
