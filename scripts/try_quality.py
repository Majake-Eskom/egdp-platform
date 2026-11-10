from pathlib import Path

import pandas as pd
import yaml

from egdp import db
from egdp.connectors import CONNECTORS
from egdp.control import registry, runlog
from egdp.layers import bronze
from egdp.quality import rules as dq

bundle_dir = Path("bundles/customer_information")
bundle = yaml.safe_load((bundle_dir / "bundle.yml").read_text())
rules = yaml.safe_load((bundle_dir / "rules.yml").read_text())
for s in bundle["sources"]:
    s["path"] = s["path"].format(landing="data/sample")

con = db.connect()
db.migrate(con)
registry.sync(con, bundle)


def run_once(plant_duplicate: bool = False) -> int:
    run_id = runlog.start_run(con, bundle["bundle"])
    status = "succeeded"
    for source in bundle["sources"]:
        name = source["name"]
        try:
            with runlog.step(con, run_id, name, "bronze") as info:
                df = CONNECTORS[source["connector"]](source)
                if plant_duplicate:
                    df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
                rows = bronze.load(con, df, source, run_id)
                info["rows_in"] = info["rows_out"] = rows

            raw = bronze.read_run(con, source, run_id)
            with runlog.step(con, run_id, name, "quality") as info:
                results = dq.check(raw, rules[name], con)
                runlog.save_dq(con, run_id, name, results)
                info["rows_in"] = len(raw)
                dq.raise_if_blocking(results)
            registry.mark_loaded(con, name)
        except Exception:
            status = "failed"  # already logged by the step
    runlog.finish_run(con, run_id, status)
    return run_id


run_once()
run_once(plant_duplicate=True)

pd.set_option("display.width", 220)
pd.set_option("display.max_columns", None)
pd.set_option("display.max_colwidth", 60)
for table in ("control_run", "control_run_step", "control_dq_result"):
    print("\n" + table)
    print(db.read(con, table))