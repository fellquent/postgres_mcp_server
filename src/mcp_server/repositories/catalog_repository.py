from typing import Any

from mcp_server.config import DbSettings
from mcp_server.repositories.connection import get_cursor


class CatalogRepository:
    """Reads schema metadata out of the database"""

    def __init__(self, db_settings: DbSettings):
        self.db_settings = db_settings

    async def execute_query(
        self, query: str, params: tuple | None = None
    ) -> list[dict[str, Any]]:
        async with get_cursor(self.db_settings) as cursor:
            await cursor.execute(query, params)
            return await cursor.fetchall()

    async def list_schemas(self) -> list[str]:
        rows = await self.execute_query(
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
        return await self.execute_query(
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
        return await self.execute_query(
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
        rows = await self.execute_query(
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
        rows = await self.execute_query(
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
