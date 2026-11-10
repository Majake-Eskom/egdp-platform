from pathlib import Path

import pandas as pd
import yaml

SECTORS = ["Mining", "Industrial", "Commercial", "Logistics", "Manufacturing"]
STAGES = ["Awaiting Engagement", "Engaging", "NDA & Information Sharing",
          "Load Profile Analysis", "Offer Preparation & Submission"]
STATUSES = ["Active", "In Progress", "Pending"]


def fake_column(target: str, n: int) -> list:
    idx = range(n)
    if target == "customer_id":
        return [f"CUS{i + 1:03d}" for i in idx]
    if target == "tracker_id":
        return [f"TRK{i + 1:03d}" for i in idx]
    if target == "customer_name":
        return [f"CUSTOMER_{chr(65 + i)}" for i in idx]
    if target == "sector":
        return [SECTORS[i % len(SECTORS)] for i in idx]
    if target == "engagement_stage":
        return [STAGES[i % len(STAGES)] for i in idx]
    if target == "opportunity_status":
        return [STATUSES[i % len(STATUSES)] for i in idx]
    if target == "annual_consumption_gwh":
        return [round(100.0 * (i + 1), 2) for i in idx]
    if target == "average_demand_mw":
        return [round(100.0 * (i + 1) / 8.76, 2) for i in idx]
    if "date" in target or target == "last_updated":
        return [pd.Timestamp("2026-10-01") + pd.Timedelta(days=i) for i in idx]
    return [f"{target} {i + 1}" for i in idx]


workbooks: dict[Path, dict[str, pd.DataFrame]] = {}
for bundle_file in sorted(Path("bundles").glob("*/bundle.yml")):
    bundle = yaml.safe_load(bundle_file.read_text())
    for s in bundle["sources"]:
        path = Path(s["path"].format(landing="data/sample"))
        n = 5 if s["key"] == ["customer_id"] else 3
        df = pd.DataFrame(
            {header: fake_column(target, n) for header, target in s["columns"].items()}
        )
        # Deliberate imperfections for later steps to catch
        if "customer_contact" in s["columns"].values():
            df.loc[1, "Customer Contact"] = "TBC"
        if "customer_group" in s["columns"].values():
            df.loc[n - 1, "Customer Group"] = None
        workbooks.setdefault(path, {})[s["sheet"]] = df

for path, sheets in workbooks.items():
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path) as writer:
        for sheet, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet, index=False)
    print("Wrote", path, "with sheets", list(sheets))