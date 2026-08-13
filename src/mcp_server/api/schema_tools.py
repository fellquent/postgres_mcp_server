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

