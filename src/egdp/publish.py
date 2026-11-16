"""Publish Gold as read-only files that Power BI, Excel and Power Apps can read.

Nothing here reads Bronze or Silver, and nothing is written back to the platform.
"""
from pathlib import Path

import pandas as pd
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

from egdp import db
from egdp.control.runlog import now

WORKBOOK = "EGDP_Gold.xlsx"
AS_OF_COLUMNS = ["bundle", "last_successful_run", "data_as_of_utc", "latest_run_status"]


def data_as_of(con) -> pd.DataFrame:
    """How fresh the published data is, per bundle.

    Gold keeps the last good data when a run fails, so readers need to see
    when the last successful run was and whether the latest one failed.
    """
    runs = pd.read_sql_query(
        "SELECT run_id, bundle, status, finished_at FROM control_run "
        "WHERE status IN ('succeeded', 'failed') ORDER BY run_id",
        con,
    )
    rows = []
    for bundle, g in runs.groupby("bundle"):
        ok = g[g["status"] == "succeeded"]
        rows.append({
            "bundle": bundle,
            "last_successful_run": int(ok["run_id"].max()) if len(ok) else None,
            "data_as_of_utc": ok["finished_at"].iloc[-1] if len(ok) else None,
            "latest_run_status": g["status"].iloc[-1],
        })
    return pd.DataFrame(rows, columns=AS_OF_COLUMNS)


def _format_sheet(ws, table_name: str, n_rows: int, n_cols: int) -> None:
    """Make the sheet an Excel Table (filter, sort, search, and usable by Power Apps)."""
    if n_rows:
        table = Table(displayName=table_name,
                      ref=f"A1:{get_column_letter(n_cols)}{n_rows + 1}")
        table.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2",
                                              showRowStripes=True)
        ws.add_table(table)
    ws.freeze_panes = "A2"
    for i, column in enumerate(ws.iter_cols(max_row=200), start=1):
        longest = max(len(str(c.value)) for c in column if c.value is not None)
        ws.column_dimensions[get_column_letter(i)].width = min(longest + 2, 50)


def publish(con, out_dir, personal: set):
    """Write every Gold table to CSV and to one Excel workbook.

    Refuses to publish anything if a Gold table contains a personal-data
    column, and checks before the first file is written.
    """
    names = db.list_tables(con, "gold")
    if not names:
        raise ValueError("no Gold tables found: run the bundles first")
    frames = {n: db.read(con, f"gold.{n}") for n in names}
    for n, df in frames.items():
        leaked = sorted(set(df.columns) & personal)
        if leaked:
            raise ValueError(f"gold.{n} exposes personal data: {leaked}")

    about = pd.DataFrame([
        {"table": n, "rows": len(df), "columns": len(df.columns),
         "published_at_utc": now()}
        for n, df in frames.items()
    ])
    as_of = data_as_of(con)
    sheets = {"_about": about, "_data_as_of": as_of, **frames}

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for name, df in sheets.items():
        df.to_csv(out / f"{name}.csv", index=False, encoding="utf-8-sig")
    with pd.ExcelWriter(out / WORKBOOK, engine="openpyxl") as writer:
        for name, df in sheets.items():
            sheet = name[:31]                      # Excel's sheet-name limit
            df.to_excel(writer, sheet_name=sheet, index=False)
            _format_sheet(writer.sheets[sheet], name.lstrip("_"), len(df), len(df.columns))
    return about, as_of