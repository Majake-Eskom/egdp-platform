from pathlib import Path
import yaml

from egdp import db
from egdp.connectors import CONNECTORS
from egdp.layers import bronze

bundle = yaml.safe_load(
    Path("bundles/customer_information/bundle.yml").read_text()
)

source = bundle["sources"][0]
source["path"] = source["path"].format(landing="data/landing")

print("SOURCE")
print(source)

print("\nREADING")

df = CONNECTORS[source["connector"]](source)

print(df.head())

print("\nCONNECTING DB")

con = db.connect()

print("\nLOADING BRONZE")

rows = bronze.load(
    con,
    df,
    source,
    run_id=999
)

print(f"{rows} rows loaded")