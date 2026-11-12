import sys

import pandas as pd

from egdp import db

pd.set_option("display.width", 220)
pd.set_option("display.max_rows", None)
pd.set_option("display.max_colwidth", 80)

con = db.connect()
n = int(sys.argv[1]) if len(sys.argv) > 1 else 10


def show(title: str, sql: str) -> None:
    print(f"\n{title}")
    df = pd.read_sql_query(sql, con, params=(n,))
    print(df.to_string(index=False) if len(df) else "  none")


show("Latest runs", """
    SELECT r.run_id, r.bundle, r.status, r.started_at, r.finished_at,
           COUNT(s.step_id) AS steps,
           COALESCE(SUM(s.status = 'failed'), 0) AS failed_steps
    FROM control_run r LEFT JOIN control_run_step s ON s.run_id = r.run_id
    GROUP BY r.run_id ORDER BY r.run_id DESC LIMIT ?""")

show("Failed steps", """
    SELECT run_id, source, layer, error, finished_at
    FROM control_run_step WHERE status = 'failed'
    ORDER BY step_id DESC LIMIT ?""")

show("Quality issues (failed > 0)", """
    SELECT run_id, source, rule, column_name, severity, failed, total
    FROM control_dq_result WHERE failed > 0
    ORDER BY run_id DESC LIMIT ?""")