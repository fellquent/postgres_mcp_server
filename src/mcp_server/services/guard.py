import sqlglot
from sqlglot import exp, parse

FORBIDDEN_NODE_TYPES = {
    exp.Insert : "INSERT",
    exp.Update : "UPDATE",
    exp.Delete : "DELETE",
    exp.Create : "CREATE",
    exp.Drop : "DROP",
    exp.Alter : "ALTER",
    exp.Command : "this statement type",
    exp.Into : "SELECT ... INTO (it creates a table)",
    exp.Lock : "FOR UPDATE / FOR SHARE (it takes row locks)"
}
FORBIDDEN_TYPES = tuple(FORBIDDEN_NODE_TYPES)


def validate_query(sql_query: str, max_rows: int) -> str:

    try:
        statements = parse(sql=sql_query, dialect="postgres")
    except sqlglot.ParseError as e:
        raise ValueError(e) from e
    
    if len(statements) != 1:
        raise ValueError(
            f"SQL query contains {len(statements)} statements, which is forbidden. Only a single SELECT statement is allowed."
        )
    
    root_node = statements[0]

    if not isinstance(root_node, (exp.Select, exp.Union)):
        raise ValueError(  # noqa: TRY004 - domain validation, not a type error
            f"Only SELECT queries are allowed; got {type(root_node).__name__.upper()}."
        )

    for node in root_node.walk():
        if isinstance(node, FORBIDDEN_TYPES):
            label = next(
                lbl for cls, lbl in FORBIDDEN_NODE_TYPES.items() if isinstance(node, cls)
            )
            raise ValueError(  # noqa: TRY004 - domain validation, not a type error
                f"{label} is not allowed. This server runs a single read-only SELECT."
            )

    existing_limit = root_node.args.get("limit")
    current = int(existing_limit.expression.name) if existing_limit else None
    if current is None or current > max_rows:
        root_node = root_node.limit(max_rows)

    return root_node.sql(dialect="postgres")
    