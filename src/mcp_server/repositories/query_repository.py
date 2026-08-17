from datetime import date, datetime, time
from decimal import Decimal
from typing import Any
from uuid import UUID

import psycopg

from mcp_server.config import DbSettings
from mcp_server.repositories.connection import get_cursor


def _coerce_value(value: Any) -> Any:
    # db types that json can't handle
    if isinstance(value, Decimal):
         # str not float, avoid precision loss
        return str(value)
    if isinstance(value, (datetime, date, time)):
        # datetime is a subclass of date; order!
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (bytes, memoryview)):
        # don't dump raw binary, just show size
        return f"<{len(value)} bytes>"
    return value

def _coerce_row(row: dict[str, Any]) -> dict[str, Any]:
    # new dict
    return {key: _coerce_value(value) for key, value in row.items()}

def _coerce_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_coerce_row(row) for row in rows]


class QueryRepository:
    """Executes validated SQL!
    This class does not check the query's safety.
    """
    def __init__(self, db_settings: DbSettings):
        self._db_settings = db_settings

    async def run_query(self, sql: str) -> list[dict[str, Any]]:
        async with get_cursor(self._db_settings) as cursor:
            try:
                await cursor.execute(sql)
            except psycopg.Error as e:
                raise ValueError(e) from e
            rows = await cursor.fetchall()
            return _coerce_rows(rows)