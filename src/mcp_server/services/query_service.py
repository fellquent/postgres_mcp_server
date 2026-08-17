import logging
from typing import Any

from mcp_server.config import Settings
from mcp_server.repositories.query_repository import QueryRepository
from mcp_server.services.guard import validate_query

logger = logging.getLogger(__name__)


class QueryService:
    def __init__(self, query_repository: QueryRepository, settings: Settings):
        self._query_repo = query_repository
        self._settings = settings

    async def run_query(self, sql: str) -> dict[str, Any]:
        # guard first; rejected sql never opens a connection
        try:
            validated = validate_query(sql, self._settings.max_rows)   # raises ValueError
        except ValueError as e:
            logger.warning("query rejected: %s | sql=%s", e, sql)
            raise
        rows = await self._query_repo.run_query(validated)

        # if number of rows == max_rows then flag it as truncated,
        # because we can't tell if it is truncated for real,
        # because we set LIMIT to a query in the validate_query() 
        if len(rows) == self._settings.max_rows:
            truncated = True
            logger.debug("result hit max_rows=%d, flagged truncated", self._settings.max_rows)
        else:
            truncated = False

        return {
            "sql" : validated,
            "rows" : rows,
            "row_count" : len(rows),
            "truncated" : truncated,
            "max_rows" : self._settings.max_rows
        }
