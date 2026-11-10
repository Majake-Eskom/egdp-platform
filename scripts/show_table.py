import sys

import pandas as pd

from egdp import db

pd.set_option("display.width", 200)
pd.set_option("display.max_rows", None)
pd.set_option("display.max_colwidth", 60)
print(db.read(db.connect(), sys.argv[1]).T)