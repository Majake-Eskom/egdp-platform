from contextlib import contextmanager
from datetime import datetime, timezone


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def start_run(con, bundle: str) -> int:
    cur = con.execute(
        "INSERT INTO control_run (bundle, started_at, status) "
        "VALUES (?, ?, 'running')",
        (bundle, now()),
    )
    con.commit()
    return cur.lastrowid


def finish_run(con, run_id: int, status: str) -> None:
    con.execute(
        "UPDATE control_run SET status=?, finished_at=? WHERE run_id=?",
        (status, now(), run_id),
    )
    con.commit()


@contextmanager
def step(con, run_id: int, source: str, layer: str):
    """Log a step's outcome, row counts and any error."""
    cur = con.execute(
        "INSERT INTO control_run_step (run_id, source, layer, status, started_at) "
        "VALUES (?, ?, ?, 'running', ?)",
        (run_id, source, layer, now()),
    )
    con.commit()
    step_id, info = cur.lastrowid, {}
    status, error = "failed", "interrupted"
    try:
        yield info
        status, error = "succeeded", None
    except Exception as exc:
        error = str(exc)
        raise
    finally:
        con.execute(
            "UPDATE control_run_step SET status=?, rows_in=?, rows_out=?, "
            "error=?, finished_at=? WHERE step_id=?",
            (status, info.get("rows_in"), info.get("rows_out"),
             error, now(), step_id),
        )
        con.commit()

def save_dq(con, run_id: int, source: str, results: list) -> None:
    con.executemany(
        "INSERT INTO control_dq_result "
        "(run_id, source, rule, column_name, severity, failed, total) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        [(run_id, source, r["rule"], r["column"], r["severity"],
          r["failed"], r["total"]) for r in results],
    )
    con.commit()