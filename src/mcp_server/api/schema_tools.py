from typing import Any

from fastmcp.exceptions import ToolError


def register(mcp, service):
    @mcp.tool
    async def list_tables(schema: str = "public") -> list[dict[str, str]]:
        """List the tables and views in a database schema.

        Call this after choosing a schema with list_schemas, or go straight
        here if you already know the schema. Use it to discover what exists
        before describing a specific table or writing a query. Only schemas
        this server is configured to expose can be inspected; asking for
        another one returns an error naming the ones that are available.

        Args:
            schema: Schema to inspect. Defaults to "public".

        Returns:
            One entry per relation, ordered by name:

                {"table_name": "books", "table_type": "table"}

            table_type is one of: "table", "partitioned table", "view",
            "materialized view", "foreign table".

            An empty list means the schema has no relations readable by this
            server -- not that the schema is missing.
        """
        try:
            return await service.list_tables(schema)
        except ValueError as e:
            raise ToolError(str(e)) from e

    @mcp.tool
    async def list_schemas() -> list[str]:
        """List the database schemas this server is allowed to inspect.

        Start here when you don't already know which schema to work in, then
        call list_tables for the one you want. The list is already filtered to
        what this server exposes -- every name returned is safe to pass to the
        other tools.

        Returns:
            Schema names, ordered by name, e.g. ["public"]
        """
        return await service.list_schemas()

    @mcp.tool
    async def describe_table(schema: str, table: str) -> dict[str, Any]:
        """Describe one table: its columns, primary key, and foreign keys.

        Call this before writing a query against a table you have not seen.
        A single call returns everything needed to write correct SQL, so there
        is no need to ask for columns and keys separately.

        Args:
            schema: Schema containing the table.
            table: Table name, case-sensitive and unquoted -- pass Orders,
                not "Orders".

        Returns:
            {
              "schema": "public",
              "table": "books",
              "columns": [
                {"column_name": "id",
                 "data_type": "integer",
                 "is_nullable": false,
                 "column_default": "nextval('books_id_seq'::regclass)",
                 "comment": null}
              ],
              "primary_key": ["id"],
              "foreign_keys": [
                {"constraint_name": "books_author_id_fkey",
                 "columns": ["author_id"],
                 "foreign_schema": "public",
                 "foreign_table": "authors",
                 "foreign_columns": ["id"]}
              ]
            }

        Notes:
            data_type carries length and precision -- "character varying(50)",
            "numeric(10,2)" -- so respect those limits when writing values.
            is_nullable is a boolean. comment is the column's COMMENT text,
            or null.
            primary_key is in key order, and is empty for views and for tables
            that have none.
            foreign_keys has one entry per constraint. columns and
            foreign_columns are parallel: position 0 references position 0.
            Views and materialized views return columns but no keys.
        """
        try:
            return await service.describe_table(schema, table)
        except ValueError as e:
            raise ToolError(str(e)) from e
