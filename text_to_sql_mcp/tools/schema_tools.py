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
    """Return Postgres native business documentation (COMMENT ON TABLE / COMMENT ON
    COLUMN text) for a table, if any has been set via SQL. Empty/null values mean
    no comment was ever added - this is not an error."""
    full_name = f"{schema}.{table_name}"
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
        "table_name": table_name,
        "table_comment": table_comment,
        "columns": columns,
    }
