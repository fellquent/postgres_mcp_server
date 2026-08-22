from typing import Any

from fastmcp.exceptions import ToolError
from fastmcp.server.auth import require_scopes


def register(mcp, service):

    @mcp.tool(auth = require_scopes("mcp-access"))
    async def run_query(query: str) -> dict[str, Any]:
        """Run one read-only SELECT and return its rows.

        Call describe_table first so column names and types are exact.

        Only a single SELECT (or UNION) is allowed. Writes, DDL, multiple
        statements, SELECT ... INTO and FOR UPDATE are rejected with an
        explanation. The database connection is read-only, so nothing can be
        modified through this tool under any circumstances.

        A LIMIT is always applied: yours is kept if it is smaller than the
        server cap, otherwise the cap replaces it.

        Args:
            query: A single SELECT statement.

        Returns:
            {
            "sql": "SELECT * FROM books LIMIT 100",   # what actually ran
            "rows": [{"title": "Forest Song", "year": 1911}],
            "row_count": 1,
            "truncated": false,
            "max_rows": 100
            }

        Notes:
            Check "truncated" before stating any total or drawing a conclusion
            about a whole table. When it is true the result was cut off at
            max_rows and more rows may exist -- narrow the query with WHERE, or
            use COUNT/SUM in SQL rather than counting the returned rows.
            Values are JSON-safe: numeric and uuid arrive as strings, dates and
            timestamps as ISO-8601 strings, binary as "<N bytes>".
        """
        try:
            return await service.run_query(query)
        except ValueError as e:
            raise ToolError(str(e)) from e