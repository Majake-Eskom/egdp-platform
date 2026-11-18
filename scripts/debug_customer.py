import yaml
from pathlib import Path

from egdp.connectors import CONNECTORS

bundle = yaml.safe_load(
    Path("bundles/customer_information/bundle.yml").read_text()
)

source = bundle["sources"][0]
source["path"] = source["path"].format(landing="data/landing")

print("Reading:")
print(source["path"])
print("Sheet:", source["sheet"])

df = CONNECTORS[source["connector"]](source)

print()
print("SUCCESS")
print()
print(df.head())
print()
print(df.columns.tolist())