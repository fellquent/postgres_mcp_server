from datetime import UTC, date, datetime, time
from decimal import Decimal
from uuid import UUID

from mcp_server.repositories.query_repository import (
    _coerce_row,
    _coerce_rows,
    _coerce_value,
)


class TestCoerceValue:
    def test_decimal_becomes_str(self):
        assert _coerce_value(Decimal("19.99")) == "19.99"

    def test_naive_datetime_becomes_isoformat(self):
        # postgres timestamp (no tz) comes back naive
        value = datetime(2026, 1, 15, 10, 30, 0) # noqa: DTZ001
        assert _coerce_value(value) == "2026-01-15T10:30:00"

    def test_aware_datetime_keeps_offset(self):
        # postgres timestamptz comes back aware
        value = datetime(2026, 1, 15, 10, 30, tzinfo=UTC)
        assert _coerce_value(value) == "2026-01-15T10:30:00+00:00"

    def test_date_becomes_isoformat(self):
        value = date(2026, 1, 15)
        assert _coerce_value(value) == "2026-01-15"

    def test_time_becomes_isoformat(self):
        value = time(10, 30, 0)
        assert _coerce_value(value) == "10:30:00"

    def test_uuid_becomes_str(self):
        value = UUID("12345678-1234-5678-1234-567812345678")
        assert _coerce_value(value) == "12345678-1234-5678-1234-567812345678"

    def test_bytes_becomes_length_marker(self):
        assert _coerce_value(b"hello") == "<5 bytes>"

    def test_memoryview_becomes_length_marker(self):
        assert _coerce_value(memoryview(b"hello world")) == "<11 bytes>"

    def test_string_unchanged(self):
        assert _coerce_value("hello") == "hello"

    def test_int_unchanged(self):
        assert _coerce_value(42) == 42

    def test_bool_unchanged(self):
        assert _coerce_value(True) is True

    def test_none_unchanged(self):
        assert _coerce_value(None) is None


class TestCoerceRow:
    def test_mixed_types_in_single_row(self):
        row = {
            "id": 1,
            "price": Decimal("19.99"),
            "created_at": datetime(2026, 1, 15, 10, 30, 0), # noqa: DTZ001
            "name": "widget",
        }
        result = _coerce_row(row)
        assert result == {
            "id": 1,    
            "price": "19.99",
            "created_at": "2026-01-15T10:30:00",
            "name": "widget",
        }

    def test_empty_row(self):
        assert _coerce_row({}) == {}


class TestCoerceRows:
    def test_multiple_rows(self):
        rows = [
            {"id": 1, "price": Decimal("10.00")},
            {"id": 2, "price": Decimal("20.00")},
        ]
        result = _coerce_rows(rows)
        assert result == [
            {"id": 1, "price": "10.00"},
            {"id": 2, "price": "20.00"},
        ]

    def test_empty_list_returns_empty_list(self):
        assert _coerce_rows([]) == []

    def test_does_not_mutate_original_rows(self):
        # coerce builds a new dict, original should stay as Decimal
        original = [{"price": Decimal("5.00")}]
        _coerce_rows(original)
        assert isinstance(original[0]["price"], Decimal)