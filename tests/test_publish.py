import shutil
from pathlib import Path

import openpyxl
import pandas as pd
import pytest

from egdp import db
from egdp.layers import gold
from egdp.publish import publish

ROOT = Path(__file__).resolve().parent.parent


def make_db():
    con = db.connect(":memory:")
    db.migrate(con, str(ROOT / "sql" / "sqlite"))
    db.write(con, pd.DataFrame({"customer_id": ["C1", "C2"],
                                "customer_name": ["Café A", "B"]}), "gold.customers")
    db.write(con, pd.DataFrame({"n": [1]}), "gold.summary")
    con.execute("INSERT INTO control_run (bundle, started_at, finished_at, status) "
                "VALUES ('b1', 't', '2026-11-10T08:00:00+00:00', 'succeeded')")
    con.execute("INSERT INTO control_run (bundle, started_at, finished_at, status) "
                "VALUES ('b1', 't', '2026-11-11T08:00:00+00:00', 'failed')")
    con.commit()
    return con


def test_publish_writes_csv_per_table_plus_about_and_freshness(tmp_path):
    publish(make_db(), tmp_path, set())
    names = {p.name for p in tmp_path.iterdir()}
    assert {"customers.csv", "summary.csv", "_about.csv",
            "_data_as_of.csv", "EGDP_Gold.xlsx"} <= names
    back = pd.read_csv(tmp_path / "customers.csv", encoding="utf-8-sig")
    assert back["customer_name"].tolist() == ["Café A", "B"]


def test_workbook_sheets_are_excel_tables_with_frozen_header(tmp_path):
    publish(make_db(), tmp_path, set())
    wb = openpyxl.load_workbook(tmp_path / "EGDP_Gold.xlsx")
    assert wb.sheetnames == ["_about", "_data_as_of", "customers", "summary"]
    ws = wb["customers"]
    assert "customers" in ws.tables
    assert ws.tables["customers"].ref == "A1:B3"
    assert ws.freeze_panes == "A2"


def test_freshness_shows_last_good_run_and_a_failed_latest_run(tmp_path):
    _, as_of = publish(make_db(), tmp_path, set())
    row = as_of.iloc[0]
    assert row["last_successful_run"] == 1
    assert row["data_as_of_utc"] == "2026-11-10T08:00:00+00:00"
    assert row["latest_run_status"] == "failed"


def test_publish_refuses_personal_data_and_writes_nothing(tmp_path):
    con = make_db()
    db.write(con, pd.DataFrame({"customer_id": ["C1"], "customer_email_address": ["x"]}),
             "gold.leaky")
    out = tmp_path / "out"
    with pytest.raises(ValueError):
        publish(con, out, {"customer_email_address"})
    assert not out.exists()


def test_publish_needs_gold_tables(tmp_path):
    con = db.connect(":memory:")
    db.migrate(con, str(ROOT / "sql" / "sqlite"))
    with pytest.raises(ValueError):
        publish(con, tmp_path, set())


def _overview_inputs(con):
    customer_cols = ["customer_key", "customer_id", "customer_name", "customer_group",
                     "sector", "province", "entity_type", "site_location",
                     "annual_consumption_gwh", "average_demand_mw", "tariff_name",
                     "ipp_name", "wheeling_type", "ppa", "carbon_reduction_targets"]
    customers = pd.DataFrame({c: [f"{c}1", f"{c}2", f"{c}3"] for c in customer_cols})
    customers["customer_id"] = ["C1", "C2", "C3"]
    customers["customer_name"] = ["Alpha", "Bravo", "Charlie"]
    customers.loc[1, "sector"] = None
    db.write(con, customers, "silver.customer")

    eng_cols = ["tracker_id", "customer_id", "engagement_stage", "opportunity_status",
                "portfolio_offered", "relationship_manager", "action_owner",
                "last_engagement_date", "latest_engagement_summary", "next_action",
                "next_action_due_date", "key_risk"]
    eng = pd.DataFrame({c: ["x", "x", "x"] for c in eng_cols})
    eng["tracker_id"] = ["T1", "T2", "T3"]
    eng["customer_id"] = ["C1", "C1", "C2"]           # C1 twice, C3 never
    eng["engagement_stage"] = ["Engaging", "Load Profile Analysis", "Engaging"]
    eng["last_engagement_date"] = ["2026-08-01", "2026-10-01", "2026-09-01"]
    eng["next_action_due_date"] = ["2026-08-15", "2999-01-01", "2026-09-15"]
    db.write(con, eng, "silver.engagement")


def test_customer_overview_is_one_row_per_customer_with_latest_engagement(tmp_path):
    con = db.connect(":memory:")
    _overview_inputs(con)
    (tmp_path / "gold").mkdir()
    shutil.copy(ROOT / "bundles/engagement_tracking/gold/customer_overview.sql",
                tmp_path / "gold")
    personal = {"contact_details", "customer_contact", "customer_contact_position",
                "customer_contact_number", "customer_email_address"}
    assert gold.build(con, tmp_path, personal) == 1      # no personal data leaks in

    ov = db.read(con, "gold.customer_overview").set_index("customer_id")
    assert list(ov.index) == ["C1", "C2", "C3"]          # one row per customer
    assert ov.loc["C1", "engagement_stage"] == "Load Profile Analysis"   # the newer one
    assert ov.loc["C1", "action_overdue"] == "No"
    assert ov.loc["C2", "action_overdue"] == "Yes"
    assert ov.loc["C3", "engagement_stage"] == "No engagement recorded"
    assert ov.loc["C3", "has_engagement"] == "No"
    assert ov.loc["C2", "sector"] == "Unassigned"