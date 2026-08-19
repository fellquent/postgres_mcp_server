import logging

from fastmcp import FastMCP
from fastmcp.server.middleware.logging import LoggingMiddleware

from mcp_server.api.query_tools import register as query_register
from mcp_server.api.schema_tools import register as schema_register
from mcp_server.config import DbSettings, Settings
from mcp_server.logging_config import configure_logging
from mcp_server.repositories.catalog_repository import CatalogRepository
from mcp_server.repositories.query_repository import QueryRepository
from mcp_server.services.introspection_service import IntrospectionService
from mcp_server.services.query_service import QueryService

# composition root
mcp = FastMCP("MCP Server")

mcp.add_middleware(
    LoggingMiddleware(
        logger=logging.getLogger("mcp_server.tools"),
        log_level=logging.INFO,
        include_payloads=True,
        max_payload_length=500
    )
)


db_settings = DbSettings()
settings = Settings()

catalog_repository = CatalogRepository(db_settings)
query_repository = QueryRepository(db_settings)

introspection_service = IntrospectionService(catalog_repository, settings)
query_service = QueryService(query_repository, settings)

schema_register(mcp, introspection_service)
query_register(mcp, query_service)


def main():
    configure_logging(settings.log_level)
    mcp.run()
