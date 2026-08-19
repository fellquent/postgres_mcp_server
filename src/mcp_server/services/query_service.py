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
            display_sql = validate_query(sql, self._settings.max_rows)   # raises ValueError
            run_sql = validate_query(sql, self._settings.max_rows + 1)   # raises ValueError

        except ValueError as e:
            logger.warning("query rejected: %s | sql=%s", e, sql)
            raise
        rows = await self._query_repo.run_query(run_sql)
        if len(rows) > self._settings.max_rows:
            truncated = True
            rows = rows[:self._settings.max_rows]
            logger.debug("result hit max_rows=%d, flagged truncated", self._settings.max_rows)
        else:
            truncated = False

        return {
            "sql" : display_sql,
            "rows" : rows,
            "row_count" : len(rows),
            "truncated" : truncated,
            "max_rows" : self._settings.max_rows
        }
