from pathlib import Path

import yaml

from egdp import db
from egdp.connectors import CONNECTORS
from egdp.layers import bronze

bundle = yaml.safe_load(
    Path("bundles/customer_information/bundle.yml").read_text()
)
source = bundle["sources"][0]
source["path"] = source["path"].format(landing="data/sample")

con = db.connect()
df = CONNECTORS[source["connector"]](source)
rows = bronze.load(con, df, source, run_id=1)

print(rows, "rows loaded to", source["bronze"])
print(bronze.read_run(con, source, 1).T)