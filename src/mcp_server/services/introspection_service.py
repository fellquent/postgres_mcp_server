import asyncio
from typing import Any

from mcp_server.config import Settings
from mcp_server.repositories.catalog_repository import CatalogRepository


class IntrospectionService:
    def __init__(self, catalog_repository: CatalogRepository, settings: Settings):
        self.catalog_repository = catalog_repository
        self.settings = settings

    def _require_allowed_schema(self, schema) -> None:
        if schema not in self.settings.allowed_schemas:
            raise ValueError(
                f"Schema '{schema}' is not allowed. Allowed: {self.settings.allowed_schemas}"
            )

    async def list_tables(self, schema: str) -> list[dict[str, str]]:
        self._require_allowed_schema(schema)
        return await self.catalog_repository.list_tables(schema)

    async def list_schemas(self) -> list[str]:
        all_schemas = await self.catalog_repository.list_schemas()
        return [
            schema for schema in all_schemas if schema in self.settings.allowed_schemas
        ]

    async def describe_table(self, schema: str, table: str) -> dict[str, Any]:
        self._require_allowed_schema(schema)
        columns, pk, fks = await asyncio.gather(
            self.catalog_repository.describe_table(schema, table),
            self.catalog_repository.get_primary_key(schema, table),
            self.catalog_repository.get_foreign_keys(schema, table),
        )
        if not columns:
            raise ValueError(
                f"Table {table} not found in schema {schema}. Use list_tables to see what exists."
            )
        return {
            "schema": schema,
            "table": table,
            "columns": columns,
            "primary_key": pk,
            "foreign_keys": fks,
        }
