import aiosqlite

from config import DATABASE_URL

SCHEMA = """
CREATE TABLE IF NOT EXISTS scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target TEXT NOT NULL,
    profile TEXT NOT NULL DEFAULT 'standard',
    status TEXT NOT NULL DEFAULT 'pending',
    started_at TEXT,
    finished_at TEXT,
    host_count INTEGER DEFAULT 0,
    error TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS hosts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id INTEGER NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    ip TEXT NOT NULL,
    hostname TEXT,
    mac TEXT,
    vendor TEXT,
    os_name TEXT,
    os_accuracy INTEGER,
    state TEXT NOT NULL DEFAULT 'up',
    node_type TEXT DEFAULT 'unknown',
    risk_score REAL DEFAULT 0,
    risk_details TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS ports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host_id INTEGER NOT NULL REFERENCES hosts(id) ON DELETE CASCADE,
    port INTEGER NOT NULL,
    protocol TEXT NOT NULL DEFAULT 'tcp',
    state TEXT NOT NULL DEFAULT 'open',
    service TEXT,
    version TEXT
);

CREATE TABLE IF NOT EXISTS traceroute_hops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host_id INTEGER NOT NULL REFERENCES hosts(id) ON DELETE CASCADE,
    hop INTEGER NOT NULL,
    ip TEXT,
    rtt REAL,
    hostname TEXT
);

CREATE TABLE IF NOT EXISTS topology_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id INTEGER NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    source_ip TEXT NOT NULL,
    target_ip TEXT NOT NULL,
    edge_type TEXT NOT NULL DEFAULT 'traceroute',
    weight REAL DEFAULT 1.0
);

CREATE INDEX IF NOT EXISTS idx_hosts_scan ON hosts(scan_id);
CREATE INDEX IF NOT EXISTS idx_hosts_scan_ip ON hosts(scan_id, ip);
CREATE INDEX IF NOT EXISTS idx_ports_host ON ports(host_id);
CREATE INDEX IF NOT EXISTS idx_hops_host ON traceroute_hops(host_id);
CREATE INDEX IF NOT EXISTS idx_edges_scan ON topology_edges(scan_id);
"""


async def load_scan_hosts(
    db: aiosqlite.Connection,
    scan_id: int,
    *,
    with_traceroute: bool = True,
) -> list[dict]:
    """Load all hosts of a scan with their ports (and optionally traceroute).

    Uses a fixed number of queries (2-3) regardless of host count, instead of
    the 2N+1 a per-host loop would issue.
    """
    cursor = await db.execute(
        "SELECT * FROM hosts WHERE scan_id=? ORDER BY id", (scan_id,)
    )
    hosts = [dict(r) for r in await cursor.fetchall()]
    if not hosts:
        return hosts

    by_id = {h["id"]: h for h in hosts}
    for host in hosts:
        host["ports"] = []
        if with_traceroute:
            host["traceroute"] = []

    host_ids = list(by_id)
    placeholders = ",".join("?" * len(host_ids))

    cursor = await db.execute(
        f"SELECT host_id, port, protocol, state, service, version "
        f"FROM ports WHERE host_id IN ({placeholders})",
        host_ids,
    )
    for row in await cursor.fetchall():
        row = dict(row)
        by_id[row.pop("host_id")]["ports"].append(row)

    if with_traceroute:
        cursor = await db.execute(
            f"SELECT host_id, hop, ip, rtt, hostname "
            f"FROM traceroute_hops WHERE host_id IN ({placeholders}) "
            f"ORDER BY host_id, hop",
            host_ids,
        )
        for row in await cursor.fetchall():
            row = dict(row)
            by_id[row.pop("host_id")]["traceroute"].append(row)

    return hosts


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(DATABASE_URL)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def init_db() -> None:
    db = await get_db()
    try:
        await db.executescript(SCHEMA)
        await db.commit()
    finally:
        await db.close()
