from sqlalchemy import text
from db.postgres import engine

with engine.connect() as conn:
    rows = conn.execute(
        text("SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema IN ('public','nltosql') ORDER BY table_schema, table_name")
    ).fetchall()
    for r in rows:
        print(r[0], r[1])
    print("---columns for nltosql.users---")
    cols = conn.execute(
        text("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='nltosql' AND table_name='users' ORDER BY ordinal_position")
    ).fetchall()
    for c in cols:
        print(c[0], c[1])
