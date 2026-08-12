from pathlib import Path
from urllib.parse import quote_plus

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

env_path = Path(__file__).resolve().parents[2] / ".env"


class DbSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=env_path,
        env_file_encoding="utf-8",
        env_prefix="DB_",
        extra="ignore",
    )

    user: str = Field(default="mcp_ro")
    password: SecretStr
    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    name: str = Field(default="playground")

    @property
    def url(self) -> str:
        # Return the UNSAFE database URL in the format: postgresql://user:password@host:port/name
        user = quote_plus(self.user)
        password = quote_plus(self.password.get_secret_value())
        return f"postgresql://{user}:{password}@{self.host}:{self.port}/{self.name}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=env_path,
        env_file_encoding="utf-8",
        env_prefix="MCP_",
        extra="ignore",
    )

    max_rows: int = Field(default=100)
    statement_timeout_ms: int = Field(default=5000)
    allowed_schemas: list[str] = Field(default_factory=lambda: ["public"])
