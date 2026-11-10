import pandas as pd

from egdp import db


class DataQualityError(Exception):
    """Raised when a blocking (error-severity) rule fails."""


def _not_null(col, rule, con):
    blank = col.astype("string").str.strip().eq("").fillna(False)
    return col.isna() | blank


def _unique(col, rule, con):
    return col.notna() & col.duplicated(keep=False)


def _allowed(col, rule, con):
    return col.notna() & ~col.isin(rule["values"])


def _positive(col, rule, con):
    num = pd.to_numeric(col, errors="coerce")
    return col.notna() & ~(num > 0)  # text and zero or negative numbers all fail


def _valid_date(col, rule, con):
    parsed = pd.to_datetime(col, errors="coerce", format="mixed")
    return col.notna() & parsed.isna()


def _referential_integrity(col, rule, con):
    ref_name = rule["reference"]
    if con is None or not db.table_exists(con, ref_name):
        raise ValueError(f"reference table {ref_name} not found; load it first")
    known = set(db.read(con, ref_name)[rule["reference_column"]].dropna())
    return col.notna() & ~col.isin(known)


RULES = {
    "not_null": _not_null,
    "unique": _unique,
    "allowed": _allowed,
    "positive": _positive,
    "valid_date": _valid_date,
    "referential_integrity": _referential_integrity,
}


def check(df: pd.DataFrame, rules: list, con=None) -> list:
    """One result per rule: how many rows failed out of how many."""
    results = []
    for rule in rules:
        name = rule["rule"]
        if name not in RULES:
            raise ValueError(f"unknown rule {name}")
        if rule["severity"] not in ("error", "warn"):
            raise ValueError(f"severity must be error or warn, got {rule['severity']}")
        if rule["column"] not in df.columns:
            raise ValueError(f"rule {name}: column {rule['column']} not in the data")
        bad = RULES[name](df[rule["column"]], rule, con)
        results.append({
            "rule": name,
            "column": rule["column"],
            "severity": rule["severity"],
            "failed": int(bad.fillna(False).sum()),
            "total": len(df),
        })
    return results


def raise_if_blocking(results: list) -> None:
    """Errors stop the load; warnings are only reported."""
    blocking = [r for r in results if r["severity"] == "error" and r["failed"]]
    if blocking:
        names = [f"{r['rule']}({r['column']})" for r in blocking]
        raise DataQualityError("blocking rules failed: " + ", ".join(names))