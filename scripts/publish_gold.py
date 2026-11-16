import argparse
import sys
from pathlib import Path

from egdp import db
from egdp.orchestrate import personal_columns
from egdp.publish import publish

parser = argparse.ArgumentParser(
    description="Publish Gold tables as read-only files for Power BI, Excel and Power Apps."
)
parser.add_argument("--out", default="exports", help="folder to write to (for example a synced SharePoint folder)")
parser.add_argument("--bundles-dir", default="bundles")
parser.add_argument("--db", default="data/egdp.db")
args = parser.parse_args()

con = db.connect(args.db)
try:
    about, as_of = publish(con, args.out, personal_columns(Path(args.bundles_dir)))
except ValueError as exc:
    print("NOT PUBLISHED:", exc)
    sys.exit(1)

for row in about.itertuples():
    print(f"{row.table:<28} {row.rows:>6} rows")
for row in as_of.itertuples():
    if row.latest_run_status == "failed":
        print(f"WARNING: the latest {row.bundle} run failed; "
              f"published data is from run {row.last_successful_run} ({row.data_as_of_utc})")
print("Published to", Path(args.out).resolve())