from pathlib import Path

import pandas as pd
import yaml

from egdp import db
from egdp.connectors import CONNECTORS
from egdp.control import registry, runlog
from egdp.layers import bronze

bundle = yaml.safe_load(
    Path("bundles/customer_information/bundle.yml").read_text()
)
for s in bundle["sources"]:
    s["path"] = s["path"].format(landing="data/sample")

con = db.connect()
db.migrate(con)
registry.sync(con, bundle)


def run_once(break_sheet: bool = False) -> int:
    run_id = runlog.start_run(con, bundle["bundle"])
    status = "succeeded"
    for source in bundle["sources"]:
        src = dict(source)
        if break_sheet:
            src["sheet"] = "Wrong_Sheet"  # simulate a bad source
        try:
            with runlog.step(con, run_id, src["name"], "bronze") as info:
                df = CONNECTORS[src["connector"]](src)
                rows = bronze.load(con, df, src, run_id)
                info["rows_in"] = info["rows_out"] = rows
            registry.mark_loaded(con, src["name"])
        except Exception:
            status = "failed"  # already logged by the step
    runlog.finish_run(con, run_id, status)
    return run_id


run_once()
run_once(break_sheet=True)

pd.set_option("display.width", 220)
pd.set_option("display.max_columns", None)
pd.set_option("display.max_colwidth", 70)
for table in ("control_source_registry", "control_run", "control_run_step"):
    print("\n" + table)
    print(db.read(con, table))