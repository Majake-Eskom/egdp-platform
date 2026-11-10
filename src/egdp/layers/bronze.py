import pandas as pd

from egdp import db


def load(con, df: pd.DataFrame, source: dict, run_id: int) -> int:
    """Append the rows exactly as received, plus four lineage columns."""
    df = df.copy()
    df["_row_hash"] = pd.util.hash_pandas_object(df, index=False).astype(str)
    df["_run_id"] = str(run_id)
    df["_source_file"] = source["path"]
    df["_loaded_at"] = pd.Timestamp.now(tz="UTC").isoformat()
    db.write(con, df, source["bronze"], mode="append")
    return len(df)


def read_run(con, source: dict, run_id: int) -> pd.DataFrame:
    return db.read(con, source["bronze"], "_run_id = ?", (str(run_id),))