import pytest

from mcp_server.services.guard import validate_query

ALLOWED_CASES = [
    (
        "SELECT * FROM users",
        100,
        "SELECT * FROM users LIMIT 100",
    ),
    (
        "SELECT id, name FROM users WHERE id = 1",
        50,
        "SELECT id, name FROM users WHERE id = 1 LIMIT 50",
    ),
    (
        "SELECT * FROM users LIMIT 10",
        100,
        "SELECT * FROM users LIMIT 10",
    ),
    (
        "SELECT * FROM users LIMIT 1000",
        100,
        "SELECT * FROM users LIMIT 100",
    ),
    (
        "SELECT * FROM users LIMIT 100",
        100,
        "SELECT * FROM users LIMIT 100",
    ),
    (
        "SELECT * FROM orders WHERE region = 'EU' ORDER BY order_no",
        20,
        "SELECT * FROM orders WHERE region = 'EU' ORDER BY order_no LIMIT 20",
    ),
    (
        "SELECT id FROM public.users UNION SELECT id FROM public.admins",
        100,
        "SELECT id FROM public.users UNION SELECT id FROM public.admins LIMIT 100",
    ),
    (
        "WITH recent AS (SELECT * FROM orders WHERE created_at > '2026-01-01') SELECT * FROM recent",
        100,
        "WITH recent AS (SELECT * FROM orders WHERE created_at > '2026-01-01') SELECT * FROM recent LIMIT 100",
    ),
]
ALLOWED_IDS = [
    "no_limit_adds_max_rows",
    "where_clause_no_limit_adds_max_rows",
    "limit_below_max_rows_unchanged",
    "limit_above_max_rows_lowered",
    "limit_equal_to_max_rows_unchanged",
    "order_by_no_limit_adds_max_rows",
    "union_query_adds_limit",
    "cte_select_adds_limit",
]

REJECTED_CASES = [
    "SELECT 1; SELECT 2",
    "SELECT * FROM users; DROP TABLE users;",
    "DELETE FROM users",
    "DELETE FROM users WHERE id = 1",
    "INSERT INTO users (id, name) VALUES (1, 'x')",
    "UPDATE users SET name = 'x' WHERE id = 1",
    "DROP TABLE users",
    "CREATE TABLE evil (id int)",
    "ALTER TABLE users ADD COLUMN evil text",
    "WITH x AS (DELETE FROM users RETURNING *) SELECT * FROM x",
    "WITH x AS (UPDATE users SET name = 'x' RETURNING *) SELECT * FROM x",
    "SELECT * FROM users FOR UPDATE",
    "TRUNCATE TABLE users",
    "SELECT FROM WHERE",
]
REJECTED_IDS = [
    "multiple_statements",
    "multiple_statements_with_drop",
    "delete_all",
    "delete_with_where",
    "insert",
    "update",
    "drop_table",
    "create_table",
    "alter_table",
    "cte_delete_trick",
    "cte_update_trick",
    "select_for_update_lock",
    "truncate",
    "invalid_syntax",
]

@pytest.mark.parametrize(
    "sql, max_rows, expected", ALLOWED_CASES, ids=ALLOWED_IDS
)
def test_allowed_cases(sql, max_rows, expected):
    assert validate_query(sql, max_rows) == expected

@pytest.mark.parametrize(
    "sql", REJECTED_CASES, ids=REJECTED_IDS
)
def test_rejected_cases(sql):
    with pytest.raises(ValueError):
        validate_query(sql, 100)