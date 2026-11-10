from pathlib import Path

import yaml

from egdp.connectors import CONNECTORS
from egdp.control import registry, runlog
from egdp.layers import bronze, silver
from egdp.quality import rules as dq


def run_source(con, source: dict, rules: dict, run_id: int) -> None:
    """Bronze -> quality gate -> Silver for one source."""
    name = source["name"]

    with runlog.step(con, run_id, name, "bronze") as info:
        df = CONNECTORS[source["connector"]](source)
        rows = bronze.load(con, df, source, run_id)
        info["rows_in"] = info["rows_out"] = rows

    raw = bronze.read_run(con, source, run_id)
    with runlog.step(con, run_id, name, "quality") as info:
        results = dq.check(raw, rules[name], con)
        runlog.save_dq(con, run_id, name, results)
        info["rows_in"] = len(raw)
        dq.raise_if_blocking(results)

    with runlog.step(con, run_id, name, "silver") as info:
        rows = silver.build(con, raw, source)
        info["rows_in"] = info["rows_out"] = rows

    registry.mark_loaded(con, name)


def run_bundle(con, bundle_dir, landing: str) -> int:
    bundle_dir = Path(bundle_dir)
    bundle = yaml.safe_load((bundle_dir / "bundle.yml").read_text())
    rules = yaml.safe_load((bundle_dir / "rules.yml").read_text())
    for s in bundle["sources"]:
        s["path"] = s["path"].format(landing=landing)

    registry.sync(con, bundle)
    run_id = runlog.start_run(con, bundle["bundle"])
    due = registry.active_sources(con, bundle["bundle"])

    failed = []
    for source in bundle["sources"]:
        if source["name"] not in due:
            continue
        try:
            run_source(con, source, rules, run_id)
        except Exception:
            failed.append(source["name"])      # already logged; carry on

    runlog.finish_run(con, run_id, "failed" if failed else "succeeded")
    return run_id