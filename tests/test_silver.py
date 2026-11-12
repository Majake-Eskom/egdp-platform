import pandas as pd

from egdp import db
from egdp.layers.silver import build, clean_company, standardise


def test_company_suffixes_are_standardised():
    out = clean_company(pd.Series(["Alpha Mining (PTY) LTD", "Beta  Limited "]))
    assert out.tolist() == ["Alpha Mining (Pty) Ltd", "Beta Ltd"]


def test_placeholder_contact_becomes_null_with_status():
    df = pd.DataFrame({"customer_contact": ["TBC", "Jane", None]})
    out = standardise(df, {"transform": {"placeholder": ["customer_contact"]}})
    assert out["customer_contact_status"].tolist() == ["TBC", "Provided", "TBC"]
    assert out["customer_contact"].isna().tolist() == [True, False, True]


def test_numbers_and_dates_are_typed():
    df = pd.DataFrame({"gwh": ["10.5", "abc", None],
                       "d": ["2026-10-01 00:00:00", "TBC", None]})
    out = standardise(df, {"transform": {"numeric": ["gwh"], "date": ["d"]}})
    assert out["gwh"].iloc[0] == 10.5
    assert out["gwh"].isna().tolist() == [False, True, True]
    assert out["d"].iloc[0] == "2026-10-01"
    assert out["d"].isna().tolist() == [False, True, True]


def test_surrogate_keys_stay_stable_between_runs():
    con = db.connect(":memory:")
    source = {"key": ["customer_id"], "silver": "silver.customer"}
    build(con, pd.DataFrame({"customer_id": ["C1", "C2"],
                             "customer_name": ["A", "B"]}), source)
    build(con, pd.DataFrame({"customer_id": ["C2", "C3"],
                             "customer_name": ["B renamed", "C"]}), source)
    keys = db.read(con, "silver.customer").set_index("customer_id")["customer_key"]
    assert keys["C2"] == 2      # kept its key although the name changed
    assert keys["C3"] == 3      # new customer gets the next key

def test_rerun_with_unchanged_customers_keeps_all_keys():
    con = db.connect(":memory:")
    source = {"key": ["customer_id"], "silver": "silver.customer"}
    df = pd.DataFrame({"customer_id": ["C1", "C2"], "customer_name": ["A", "B"]})
    build(con, df, source)
    build(con, df, source)
    keys = db.read(con, "silver.customer").sort_values("customer_id")["customer_key"]
    assert keys.tolist() == [1, 2]