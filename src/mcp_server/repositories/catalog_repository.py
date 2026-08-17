import logging
import time
from typing import Any

from mcp_server.config import DbSettings
from mcp_server.repositories.connection import get_cursor

logger = logging.getLogger(__name__)


class CatalogRepository:
    """Reads schema metadata out of the database

    Uses pg_catalog rather than information_schema wherever constraints are
    involved: those views are filtered by ownership and by privileges other
    than SELECT, so they return nothing at all for a read-only role.
    """

    def __init__(self, db_settings: DbSettings):
        self._db_settings = db_settings

    async def _execute_query(
        self, query: str, params: tuple | None = None
    ) -> list[dict[str, Any]]:
        # one place covers every catalog query; DEBUG because these are spam
        # unless something is slow
        started = time.perf_counter()
        async with get_cursor(self._db_settings) as cursor:
            await cursor.execute(query, params)
            rows = await cursor.fetchall()
            logger.debug(
                "catalog query: %d rows in %.1f ms | params=%s",
                len(rows),
                (time.perf_counter() - started) * 1000,
                params,
            )
            return rows

    async def list_schemas(self) -> list[str]:
        rows = await self._execute_query(
            """
            SELECT nspname AS schema_name
            FROM pg_namespace
            WHERE nspname !~ '^pg_'
              AND nspname <> 'information_schema'
              AND has_schema_privilege(nspname, 'USAGE')
            ORDER BY nspname
            """,
        )
        return [row["schema_name"] for row in rows]

    async def list_tables(self, schema: str) -> list[dict[str, str]]:
        # pg_class, not information_schema.tables: that view omits materialized
        # views entirely. has_table_privilege replaces the privilege filtering
        # information_schema was doing for us implicitly.
        return await self._execute_query(
            """
            SELECT
                cl.relname AS table_name,
                CASE cl.relkind
                    WHEN 'r' THEN 'table'
                    WHEN 'p' THEN 'partitioned table'
                    WHEN 'v' THEN 'view'
                    WHEN 'm' THEN 'materialized view'
                    WHEN 'f' THEN 'foreign table'
                END AS table_type
            FROM pg_class cl
            JOIN pg_namespace nsp ON nsp.oid = cl.relnamespace
            WHERE nsp.nspname = %s
              AND cl.relkind IN ('r', 'p', 'v', 'm', 'f')
              AND has_table_privilege(cl.oid, 'SELECT')
            ORDER BY cl.relname
            """,
            (schema,),
        )

    async def describe_table(self, schema: str, table: str) -> list[dict[str, Any]]:
        # format_type keeps length and precision - character varying(50),
        # numeric(10,2) - which information_schema.data_type throws away.
        # attnum > 0 skips system columns; attisdropped skips the tombstones
        # dropped columns leave behind.
        return await self._execute_query(
            """
            SELECT
                att.attname                               AS column_name,
                format_type(att.atttypid, att.atttypmod)  AS data_type,
                NOT att.attnotnull                        AS is_nullable,
                pg_get_expr(def.adbin, def.adrelid)       AS column_default,
                col_description(att.attrelid, att.attnum) AS comment
            FROM pg_attribute att
            JOIN pg_class     cl  ON cl.oid  = att.attrelid
            JOIN pg_namespace nsp ON nsp.oid = cl.relnamespace
            LEFT JOIN pg_attrdef def
                ON def.adrelid = att.attrelid AND def.adnum = att.attnum
            WHERE nsp.nspname = %s
              AND cl.relname  = %s
              AND att.attnum > 0
              AND NOT att.attisdropped
            ORDER BY att.attnum
            """,
            (schema, table),
        )

    async def get_primary_key(self, schema: str, table: str) -> list[str]:
        # conkey holds column positions; unnesting WITH ORDINALITY preserves
        # key order, which matters for composite keys.
        # relname is compared as an exact string, so "Orders" and "orders" stay
        # distinct - a ::regclass cast would fold the case and answer about
        # the wrong table.
        rows = await self._execute_query(
            """
            SELECT att.attname AS column_name
            FROM pg_constraint con
            JOIN pg_class     cl  ON cl.oid  = con.conrelid
            JOIN pg_namespace nsp ON nsp.oid = cl.relnamespace
            JOIN LATERAL unnest(con.conkey) WITH ORDINALITY AS k(attnum, ord)
                ON TRUE
            JOIN pg_attribute att
                ON att.attrelid = con.conrelid AND att.attnum = k.attnum
            WHERE con.contype = 'p'
              AND nsp.nspname = %s
              AND cl.relname  = %s
            ORDER BY k.ord
            """,
            (schema, table),
        )
        return [row["column_name"] for row in rows]

    async def get_foreign_keys(self, schema: str, table: str) -> list[dict[str, Any]]:
        # conkey and confkey are parallel arrays of column positions; unnesting
        # both together pairs each local column with the right foreign one.
        # Joining them separately produces a cartesian product - a two-column
        # key would come back as four rows with three of the pairs invented.
        rows = await self._execute_query(
            """
            SELECT
                con.conname   AS constraint_name,
                att.attname   AS column_name,
                nsp_f.nspname AS foreign_schema,
                cl_f.relname  AS foreign_table,
                att_f.attname AS foreign_column
            FROM pg_constraint con
            JOIN pg_class     cl    ON cl.oid    = con.conrelid
            JOIN pg_namespace nsp   ON nsp.oid   = cl.relnamespace
            JOIN pg_class     cl_f  ON cl_f.oid  = con.confrelid
            JOIN pg_namespace nsp_f ON nsp_f.oid = cl_f.relnamespace
            JOIN LATERAL unnest(con.conkey, con.confkey) WITH ORDINALITY
                AS k(local_att, foreign_att, ord) ON TRUE
            JOIN pg_attribute att
                ON att.attrelid   = con.conrelid  AND att.attnum   = k.local_att
            JOIN pg_attribute att_f
                ON att_f.attrelid = con.confrelid AND att_f.attnum = k.foreign_att
            WHERE con.contype = 'f'
              AND nsp.nspname = %s
              AND cl.relname  = %s
            ORDER BY con.conname, k.ord
            """,
            (schema, table),
        )
        return self._group_foreign_keys(rows)

    @staticmethod
    def _group_foreign_keys(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        # the query returns one row per column; callers want one entry per
        # constraint, with columns and foreign_columns parallel
        grouped: dict[str, dict[str, Any]] = {}
        for row in rows:
            key = row["constraint_name"]
            if key not in grouped:
                grouped[key] = {
                    "constraint_name": key,
                    "columns": [],
                    "foreign_schema": row["foreign_schema"],
                    "foreign_table": row["foreign_table"],
                    "foreign_columns": [],
                }
            grouped[key]["columns"].append(row["column_name"])
            grouped[key]["foreign_columns"].append(row["foreign_column"])
        return list(grouped.values())
