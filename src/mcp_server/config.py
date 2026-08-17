from pathlib import Path
from urllib.parse import quote_plus

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# absolute, not ".env": a stdio server is spawned with an unpredictable cwd
env_path = Path(__file__).resolve().parents[2] / ".env"


class DbSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=env_path,
        env_file_encoding="utf-8",
        env_prefix="DB_",
        extra="ignore",
    )

    user: str = Field(default="mcp_ro")
    # no default: a missing password should fail at startup, not connect somewhere else
    password: SecretStr
    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    name: str = Field(default="playground")
    statement_timeout_ms: int = Field(default=5000)

    @property
    def url(self) -> str:
        # Return the UNSAFE database URL in the format: postgresql://user:password@host:port/name
        # quote_plus: a / # or ? in the password would otherwise corrupt the url
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
    allowed_schemas: list[str] = Field(default_factory=lambda: ["public"])
