import pytest
from pydantic import ValidationError
from pydantic_settings import SettingsError

from mcp_server.config import DbSettings, Settings

# ========== Test Cases for DbSettings ==========


def test_url_generation():
    db = DbSettings(
        _env_file=None,
        user="test_user",
        password="test_password",
        host="test_host",
        port=1234,
        name="test_db",
    )
    assert db.url == "postgresql://test_user:test_password@test_host:1234/test_db"


def test_url_generation_with_special_characters():
    db = DbSettings(
        _env_file=None,
        user="test_user",
        password="pa/ss",
        host="test_host",
        port=1234,
        name="test_db",
    )
    assert "pa%2Fss" in db.url  # Ensure the password is URL-encoded
    assert "pa/ss" not in db.url  # Ensure the raw password is not in the URL


def test_missing_password(monkeypatch):
    monkeypatch.delenv("DB_PASSWORD", raising=False)

    with pytest.raises(ValidationError, match="password"):
        DbSettings(
            _env_file=None,
            user="test_user",
            host="test_host",
            port=1234,
            name="test_db",
        )


def test_env_vars_override(monkeypatch):
    monkeypatch.setenv("DB_USER", "env_user")
    monkeypatch.setenv("DB_PASSWORD", "env_password")
    monkeypatch.setenv("DB_HOST", "env_host")
    monkeypatch.setenv("DB_PORT", "5678")
    monkeypatch.setenv("DB_NAME", "env_db")

    db = DbSettings()
    assert db.user == "env_user"
    assert db.password.get_secret_value() == "env_password"
    assert db.host == "env_host"
    assert db.port == 5678
    assert db.name == "env_db"


# ========= Test Cases for Settings ==========


def test_settings_defaults(monkeypatch):
    monkeypatch.delenv("MCP_MAX_ROWS", raising=False)
    monkeypatch.delenv("MCP_STATEMENT_TIMEOUT_MS", raising=False)
    monkeypatch.delenv("MCP_ALLOWED_SCHEMAS", raising=False)

    settings = Settings(_env_file=None)
    assert settings.max_rows == 100
    assert settings.statement_timeout_ms == 5000
    assert settings.allowed_schemas == ["public"]


def test_settings_env_vars_type(monkeypatch):
    monkeypatch.setenv("MCP_MAX_ROWS", "7")
    monkeypatch.setenv("MCP_STATEMENT_TIMEOUT_MS", "123")
    monkeypatch.setenv("MCP_ALLOWED_SCHEMAS", '["public", "my_schema"]')

    settings = Settings(_env_file=None)
    assert settings.max_rows == 7
    assert settings.statement_timeout_ms == 123
    assert settings.allowed_schemas == ["public", "my_schema"]
    assert isinstance(settings.allowed_schemas, list)


def test_settings_invalid_allowed_schemas(monkeypatch):
    monkeypatch.setenv("MCP_ALLOWED_SCHEMAS", "public")
    with pytest.raises(SettingsError, match="allowed_schemas"):
        Settings(_env_file=None)
