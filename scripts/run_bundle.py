import argparse
import logging
import sys
import time
from pathlib import Path

from egdp import db
from egdp.orchestrate import run_bundle

parser = argparse.ArgumentParser(description="Run one or more bundles in order.")
parser.add_argument("bundles", nargs="+", help="bundle folder names, run in this order")
parser.add_argument("--landing", default="data/landing")
parser.add_argument("--bundles-dir", default="bundles")
parser.add_argument("--db", default="data/egdp.db")
parser.add_argument("--log", default="logs/egdp.log")
args = parser.parse_args()

Path(args.log).parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=args.log, level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logging.Formatter.converter = time.gmtime

con = db.connect(args.db)
db.migrate(con)

exit_code = 0
for name in args.bundles:
    run_id = run_bundle(con, Path(args.bundles_dir) / name, args.landing)
    status = con.execute(
        "SELECT status FROM control_run WHERE run_id=?", (run_id,)
    ).fetchone()[0]
    print(f"{name}: run {run_id} {status}")
    if status == "failed":
        for source, layer, error in con.execute(
            "SELECT source, layer, error FROM control_run_step "
            "WHERE run_id=? AND status='failed'", (run_id,)
        ):
            print(f"  FAILED {source} / {layer}: {error}")
        print("Stopping: later bundles depend on this one.")
        exit_code = 1
        break

sys.exit(exit_code)