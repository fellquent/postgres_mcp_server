from mcp_server.config import Settings
from mcp_server.repositories.catalog_repository import CatalogRepository


class IntrospectionService:
    def __init__(self, catalog_repository: CatalogRepository, settings: Settings):
        self.catalog_repository = catalog_repository
        self.settings = settings

    async def list_tables(self, schema: str) -> list[dict[str, str]]:
        if schema in self.settings.allowed_schemas:
            return await self.catalog_repository.list_tables(schema)
        else:
            raise ValueError(
                f"Schema '{schema}' is not allowed. Allowed: {self.settings.allowed_schemas}"
            )

    async def list_schemas(self) -> list[str]:
        all_schemas = await self.catalog_repository.list_schemas()
        return [schema for schema in all_schemas if schema in self.settings.allowed_schemas]
