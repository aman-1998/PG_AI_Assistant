"""Schema discovery tools: schemas, tables, describe table."""
from db_utils import fetch_all
from mcp_instance import mcp


@mcp.tool()
def list_schemas() -> list[dict]:
    """List all non-system schemas in the connected Postgres database."""
    sql = """
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
          AND schema_name NOT LIKE 'pg_toast%'
          AND schema_name NOT LIKE 'pg_temp%'
        ORDER BY schema_name
    """
    return fetch_all(sql)


@mcp.tool()
def list_tables(schema: str = "public") -> list[dict]:
    """List all tables (and views) in the given schema."""
    sql = """
        SELECT table_name, table_type
        FROM information_schema.tables
        WHERE table_schema = %s
        ORDER BY table_name
    """
    return fetch_all(sql, (schema,))


@mcp.tool()
def describe_table(table_name: str, schema: str = "public") -> dict:
    """Describe a table: columns (name/type/nullable/default) and primary key columns."""
    columns_sql = """
        SELECT column_name, data_type, is_nullable, column_default, character_maximum_length
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position
    """
    pk_sql = """
        SELECT kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
        WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_schema = %s AND tc.table_name = %s
    """
    columns = fetch_all(columns_sql, (schema, table_name))
    primary_key = [row["column_name"] for row in fetch_all(pk_sql, (schema, table_name))]
    return {"schema": schema, "table_name": table_name, "columns": columns, "primary_key": primary_key}


@mcp.tool()
def get_table_comments(table_name: str, schema: str = "public") -> dict:
    """Return Postgres native business documentation (COMMENT ON SCHEMA / COMMENT ON
    TABLE / COMMENT ON COLUMN text) for a table, if any has been set via SQL. Empty/
    null values mean no comment was ever added - this is not an error; in that case
    fall back to reasoning from the table name and column names/comments instead."""
    full_name = f"{schema}.{table_name}"
    schema_comment_rows = fetch_all(
        "SELECT obj_description(to_regnamespace(%s), 'pg_namespace') AS comment", (schema,)
    )
    schema_comment = schema_comment_rows[0]["comment"] if schema_comment_rows else None

    table_comment_rows = fetch_all(
        "SELECT obj_description(to_regclass(%s), 'pg_class') AS comment", (full_name,)
    )
    table_comment = table_comment_rows[0]["comment"] if table_comment_rows else None

    columns_sql = """
        SELECT a.attname AS column_name, col_description(a.attrelid, a.attnum) AS comment
        FROM pg_attribute a
        WHERE a.attrelid = to_regclass(%s) AND a.attnum > 0 AND NOT a.attisdropped
        ORDER BY a.attnum
    """
    columns = fetch_all(columns_sql, (full_name,))
    return {
        "schema": schema,
        "schema_comment": schema_comment,
        "table_name": table_name,
        "table_comment": table_comment,
        "columns": columns,
    }


@mcp.tool()
def list_table_comments(schema: str = "public") -> dict:
    """Return Postgres native business documentation - the schema's own COMMENT ON
    SCHEMA text, plus COMMENT ON TABLE / COMMENT ON COLUMN text for EVERY table in
    the given schema - in one call. Use this to discover which table(s)/column(s)
    are relevant to a business question (e.g. "website traffic", "sales",
    "revenue") when the user didn't name exact tables, instead of calling
    get_table_comments one table at a time. Tables/columns with no comment set are
    still included with a null comment (not an error) - a schema with sparse or no
    comments is common. When a table's table_comment is null/empty, do NOT skip
    it - infer its likely purpose from its table_name and its columns' names and
    comments instead (e.g. a table named `page_views` with columns `session_id`,
    `url`, `viewed_at` is very likely relevant to a "website traffic" question
    even with zero comments set).
    """
    schema_comment_rows = fetch_all(
        "SELECT obj_description(to_regnamespace(%s), 'pg_namespace') AS comment", (schema,)
    )
    schema_comment = schema_comment_rows[0]["comment"] if schema_comment_rows else None

    table_comment_rows = fetch_all(
        """
        SELECT c.relname AS table_name, obj_description(c.oid, 'pg_class') AS table_comment
        FROM pg_catalog.pg_class c
        JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = %s AND c.relkind IN ('r', 'v', 'm', 'p')
        ORDER BY c.relname
        """,
        (schema,),
    )
    column_comment_rows = fetch_all(
        """
        SELECT c.relname AS table_name, a.attname AS column_name,
               col_description(a.attrelid, a.attnum) AS comment
        FROM pg_catalog.pg_attribute a
        JOIN pg_catalog.pg_class c ON c.oid = a.attrelid
        JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = %s AND c.relkind IN ('r', 'v', 'm', 'p')
          AND a.attnum > 0 AND NOT a.attisdropped
        ORDER BY c.relname, a.attnum
        """,
        (schema,),
    )
    columns_by_table: dict[str, list[dict]] = {}
    for row in column_comment_rows:
        columns_by_table.setdefault(row["table_name"], []).append(
            {"column_name": row["column_name"], "comment": row["comment"]}
        )

    return {
        "schema": schema,
        "schema_comment": schema_comment,
        "tables": [
            {
                "table_name": row["table_name"],
                "table_comment": row["table_comment"],
                "columns": columns_by_table.get(row["table_name"], []),
            }
            for row in table_comment_rows
        ],
    }

