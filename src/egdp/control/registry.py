from egdp.control.runlog import now


def sync(con, bundle: dict) -> None:
    """Make the registry match the bundle file (keeps active and last_loaded)."""
    for s in bundle["sources"]:
        con.execute(
            "INSERT INTO control_source_registry "
            "(source, bundle, connector, refresh, owner) VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(source) DO UPDATE SET bundle=excluded.bundle, "
            "connector=excluded.connector, refresh=excluded.refresh, "
            "owner=excluded.owner",
            (s["name"], bundle["bundle"], s["connector"],
             bundle.get("schedule"), bundle.get("owner")),
        )
    con.commit()


def active_sources(con, bundle_name: str) -> list[str]:
    rows = con.execute(
        "SELECT source FROM control_source_registry "
        "WHERE bundle=? AND active=1",
        (bundle_name,),
    )
    return [r[0] for r in rows]


def mark_loaded(con, source: str) -> None:
    con.execute(
        "UPDATE control_source_registry SET last_loaded=? WHERE source=?",
        (now(), source),
    )
    con.commit()