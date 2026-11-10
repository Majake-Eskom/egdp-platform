import pandas as pd
import pytest

from egdp import db
from egdp.quality.rules import DataQualityError, check, raise_if_blocking


def rule(name, column, severity="error", **extra):
    return {"rule": name, "column": column, "severity": severity, **extra}


def failed(df, r, con=None):
    return check(df, [r], con)[0]["failed"]


def test_not_null_flags_missing_and_blank():
    df = pd.DataFrame({"a": ["x", None, "  "]})
    assert failed(df, rule("not_null", "a")) == 2


def test_unique_flags_both_duplicates():
    df = pd.DataFrame({"a": ["C1", "C1", "C2"]})
    assert failed(df, rule("unique", "a")) == 2


def test_unique_ignores_missing_values():
    df = pd.DataFrame({"a": [None, None, "C1"]})
    assert failed(df, rule("unique", "a")) == 0


def test_allowed_flags_unlisted_values():
    df = pd.DataFrame({"a": ["Mining", "Retail", None]})
    assert failed(df, rule("allowed", "a", values=["Mining"])) == 1


def test_positive_flags_zero_negative_and_text():
    df = pd.DataFrame({"a": ["10", "0", "-5", "abc", None]})
    assert failed(df, rule("positive", "a")) == 3


def test_valid_date_flags_text():
    df = pd.DataFrame({"a": ["2026-10-01", "TBC", None]})
    assert failed(df, rule("valid_date", "a")) == 1


def test_referential_integrity_flags_unknown_ids():
    con = db.connect(":memory:")
    db.write(con, pd.DataFrame({"customer_id": ["CUS001", "CUS002"]}),
             "silver.customer")
    df = pd.DataFrame({"customer_id": ["CUS001", "CUS999"]})
    r = rule("referential_integrity", "customer_id",
             reference="silver.customer", reference_column="customer_id")
    assert failed(df, r, con) == 1


def test_referential_integrity_needs_the_reference_table():
    con = db.connect(":memory:")
    df = pd.DataFrame({"customer_id": ["CUS001"]})
    r = rule("referential_integrity", "customer_id",
             reference="silver.customer", reference_column="customer_id")
    with pytest.raises(ValueError):
        check(df, [r], con)


def test_unknown_rule_and_missing_column_raise():
    df = pd.DataFrame({"a": ["x"]})
    with pytest.raises(ValueError):
        check(df, [rule("made_up", "a")])
    with pytest.raises(ValueError):
        check(df, [rule("not_null", "nope")])


def test_error_blocks_but_warning_does_not():
    results = [{"rule": "unique", "column": "a", "severity": "warn",
                "failed": 2, "total": 3}]
    raise_if_blocking(results)  # warning: no exception
    results[0]["severity"] = "error"
    with pytest.raises(DataQualityError):
        raise_if_blocking(results)