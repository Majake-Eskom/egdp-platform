import re
import sqlite3
from pathlib import Path

import pandas as pd


def connect(path: str = "data/egdp.db"):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(path)


def table_name(name: str) -> str:
    """SQLite has no schemas, so bronze.customer_master becomes bronze_customer_master."""
    return name.replace(".", "_")


def write(con, df: pd.DataFrame, name: str, mode: str = "append") -> None:
    df.to_sql(table_name(name), con, if_exists=mode, index=False)
    con.commit()


def read(con, name: str, where: str = "", params: tuple = ()) -> pd.DataFrame:
    sql = f"SELECT * FROM {table_name(name)}"
    if where:
        sql += f" WHERE {where}"
    return pd.read_sql_query(sql, con, params=params)


def migrate(con, folder: str = "sql/sqlite") -> None:
    """Apply numbered migration files in order, each exactly once."""
    con.execute(
        "CREATE TABLE IF NOT EXISTS schema_migration "
        "(version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
    )
    done = {row[0] for row in con.execute("SELECT version FROM schema_migration")}
    for path in sorted(Path(folder).glob("V*.sql")):
        if path.name in done:
            continue
        con.executescript(path.read_text())
        con.execute(
            "INSERT INTO schema_migration VALUES (?, datetime('now'))",
            (path.name,),
        )
        con.commit()


def table_exists(con, name: str) -> bool:
    row = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table_name(name),),
    ).fetchone()
    return row is not None


def render(sql: str) -> str:
    """Swap {schema.table} placeholders for the real table names."""
    return re.sub(r"\{(\w+\.\w+)\}", lambda m: table_name(m.group(1)), sql)


def list_tables(con, schema: str) -> list[str]:
    """Table names in a schema (SQLite: tables with that prefix), without the prefix."""
    prefix = f"{schema}_"
    rows = con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    return [r[0][len(prefix):] for r in rows
            if r[0].startswith(prefix) and not r[0].endswith("__new")]