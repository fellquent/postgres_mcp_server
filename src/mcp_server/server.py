from fastmcp import FastMCP
from mcp_server.config import DbSettings, Settings
from mcp_server.repositories.catalog_repository import CatalogRepository
from mcp_server.services.introspection_service import IntrospectionService
from mcp_server.api.schema_tools import register

mcp = FastMCP("MCP Server")

db_settings = DbSettings()
settings = Settings()

catalog_repository = CatalogRepository(db_settings)
introspection_service = IntrospectionService(catalog_repository, settings)

register(mcp, introspection_service)


def main():
    mcp.run()
