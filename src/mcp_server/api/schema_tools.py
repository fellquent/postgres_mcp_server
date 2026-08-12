from fastmcp.exceptions import ToolError


def register(mcp, service):
    @mcp.tool
    async def list_tables(schema: str = "public") -> list[dict[str, str]]:
        """List the tables and views in a database schema.

        Use this first, to discover what exists before describing a specific
        table or writing a query. Only schemas this server is configured to
        expose can be inspected; asking for another one returns an error
        naming the ones that are available.

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
