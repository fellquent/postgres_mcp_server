from fastmcp import FastMCP

from mcp_server.api.query_tools import register as query_register
from mcp_server.api.schema_tools import register as schema_register
from mcp_server.config import DbSettings, Settings
from mcp_server.repositories.catalog_repository import CatalogRepository
from mcp_server.repositories.query_repository import QueryRepository
from mcp_server.services.introspection_service import IntrospectionService
from mcp_server.services.query_service import QueryService

mcp = FastMCP("MCP Server")

db_settings = DbSettings()
settings = Settings()

catalog_repository = CatalogRepository(db_settings)
query_repository = QueryRepository(db_settings)

introspection_service = IntrospectionService(catalog_repository, settings)
query_service = QueryService(query_repository, settings)

schema_register(mcp, introspection_service)
query_register(mcp, query_service)


def main():
    mcp.run()
