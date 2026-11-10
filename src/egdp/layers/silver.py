import re

import pandas as pd

from egdp import db

PLACEHOLDERS = {"", "TBC", "TBD", "N/A", "NA", "NONE", "UNKNOWN", "-"}


def clean_text(s: pd.Series) -> pd.Series:
    """Trim, collapse repeated spaces, and turn empty text into a null."""
    s = s.astype("string").str.strip().str.replace(r"\s+", " ", regex=True)
    return s.mask(s.eq("").fillna(False))


def clean_company(s: pd.Series) -> pd.Series:
    """One spelling for company suffixes: (Pty) and Ltd."""
    s = clean_text(s)
    s = s.str.replace(r"\(pty\)", "(Pty)", flags=re.I, regex=True)
    return s.str.replace(r"\b(ltd|limited)\b", "Ltd", flags=re.I, regex=True)


def is_placeholder(s: pd.Series) -> pd.Series:
    t = s.astype("string").str.strip().str.upper()
    return t.isna() | t.isin(PLACEHOLDERS)


def standardise(df: pd.DataFrame, source: dict) -> pd.DataFrame:
    cfg = source.get("transform") or {}
    out = df[[c for c in df.columns if c != "_row_hash"]].copy()

    for c in out.columns:
        if not c.startswith("_"):          # keep lineage columns as they are
            out[c] = clean_text(out[c])
    for c in cfg.get("company_name", []):
        out[c] = clean_company(out[c])
    for c in cfg.get("numeric", []):
        out[c] = pd.to_numeric(out[c], errors="coerce")
    for c in cfg.get("date", []):
        parsed = pd.to_datetime(out[c], errors="coerce", format="mixed")
        out[c] = parsed.dt.strftime("%Y-%m-%d")
    for c in cfg.get("placeholder", []):
        missing = is_placeholder(out[c])
        out[f"{c}_status"] = missing.map({True: "TBC", False: "Provided"})
        out.loc[missing, c] = None
    return out


def assign_keys(con, df: pd.DataFrame, source: dict) -> pd.DataFrame:
    """Give each entity a surrogate key that stays the same between runs."""
    table = source["silver"]
    key_col = table.split(".")[-1] + "_key"        # silver.customer -> customer_key
    natural = list(source["key"])

    if db.table_exists(con, table):
        old = db.read(con, table)[natural + [key_col]].drop_duplicates(natural)
        df = df.merge(old, on=natural, how="left")
        start = int(old[key_col].max()) + 1 if len(old) else 1
    else:
        df = df.copy()
        df[key_col] = float("nan")
        start = 1

    missing = df[key_col].isna()
    df.loc[missing, key_col] = list(range(start, start + int(missing.sum())))
    df[key_col] = df[key_col].astype(int)
    return df[[key_col] + [c for c in df.columns if c != key_col]]


def build(con, raw: pd.DataFrame, source: dict) -> int:
    """Silver holds the current state: rebuilt from the run that passed the gate."""
    out = assign_keys(con, standardise(raw, source), source)
    db.write(con, out, source["silver"], mode="replace")
    return len(out)