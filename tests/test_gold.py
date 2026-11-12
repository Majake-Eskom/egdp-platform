import pandas as pd
import pytest

from egdp import db
from egdp.layers import gold


def make_bundle(tmp_path, sql):
    (tmp_path / "gold").mkdir(exist_ok=True)
    (tmp_path / "gold" / "summary.sql").write_text(sql)
    return tmp_path


def silver_customers(con, **extra):
    df = pd.DataFrame({"customer_id": ["C1", "C2"], **extra})
    db.write(con, df, "silver.customer")


def test_render_swaps_schema_placeholders():
    assert db.render("SELECT * FROM {silver.customer}") == "SELECT * FROM silver_customer"


def test_gold_table_is_built_from_silver(tmp_path):
    con = db.connect(":memory:")
    silver_customers(con)
    bundle_dir = make_bundle(tmp_path, "SELECT COUNT(*) AS n FROM {silver.customer}")
    assert gold.build(con, bundle_dir, set()) == 1
    assert db.read(con, "gold.summary")["n"].iloc[0] == 2


def test_gold_refuses_personal_data_columns(tmp_path):
    con = db.connect(":memory:")
    silver_customers(con, contact_details=["a", "b"])
    bundle_dir = make_bundle(
        tmp_path, "SELECT customer_id, contact_details FROM {silver.customer}"
    )
    with pytest.raises(ValueError):
        gold.build(con, bundle_dir, {"contact_details"})
    assert not db.table_exists(con, "gold.summary")


def test_failed_rebuild_keeps_the_last_good_table(tmp_path):
    con = db.connect(":memory:")
    silver_customers(con)
    bundle_dir = make_bundle(tmp_path, "SELECT COUNT(*) AS n FROM {silver.customer}")
    gold.build(con, bundle_dir, set())

    make_bundle(tmp_path, "SELECT no_such_column FROM {silver.customer}")
    with pytest.raises(Exception):
        gold.build(con, bundle_dir, set())
    assert db.read(con, "gold.summary")["n"].iloc[0] == 2