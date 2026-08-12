from contextlib import asynccontextmanager

import psycopg
from psycopg.rows import dict_row

from mcp_server.config import DbSettings


# TODO: add a connection pool
@asynccontextmanager
async def get_cursor(db_settings: DbSettings):
    connection = await psycopg.AsyncConnection.connect(
        db_settings.url,
        row_factory=dict_row,
        options=(
            "-c default_transaction_read_only=on "
            f"-c statement_timeout={db_settings.statement_timeout_ms}"
        ),
    )
    try:
        async with connection.cursor() as cursor:
            yield cursor
    finally:
        # rollback can itself fail if the connection died; still close it
        try:
            await connection.rollback()
        finally:
            await connection.close()
