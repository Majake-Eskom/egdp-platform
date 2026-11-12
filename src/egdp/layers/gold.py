from pathlib import Path

from egdp import db


def build(con, bundle_dir, personal: set) -> int:
    """Rebuild every Gold table from the .sql files in the bundle's gold folder.

    Each table is built under a temporary name and swapped in only when it is
    complete, so a failure leaves the last good table in place. A table that
    exposes a personal-data column is refused.
    """
    built = 0
    for path in sorted((Path(bundle_dir) / "gold").glob("*.sql")):
        table = db.table_name(f"gold.{path.stem}")
        tmp = f"{table}__new"
        con.execute(f"DROP TABLE IF EXISTS {tmp}")
        con.execute(f"CREATE TABLE {tmp} AS {db.render(path.read_text())}")

        columns = {row[1] for row in con.execute(f"PRAGMA table_info({tmp})")}
        leaked = sorted(columns & personal)
        if leaked:
            con.execute(f"DROP TABLE {tmp}")
            raise ValueError(f"gold.{path.stem} exposes personal data: {leaked}")

        con.execute(f"DROP TABLE IF EXISTS {table}")
        con.execute(f"ALTER TABLE {tmp} RENAME TO {table}")
        con.commit()
        built += 1
    return built