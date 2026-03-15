from __future__ import annotations

import logging
from typing import Any

import aiosqlite

logger = logging.getLogger(__name__)


async def load_hosts_with_data(db: aiosqlite.Connection, scan_id: int) -> list[dict[str, Any]]:
    """Load hosts with ports and traceroute using batched queries (avoids N+1)."""
    cursor = await db.execute("SELECT * FROM hosts WHERE scan_id=?", (scan_id,))
    host_rows = await cursor.fetchall()
    if not host_rows:
        return []

    hosts_by_id: dict[int, dict[str, Any]] = {}
    for row in host_rows:
        h = dict(row)
        h["ports"] = []
        h["traceroute"] = []
        hosts_by_id[h["id"]] = h

    host_ids = list(hosts_by_id.keys())
    placeholders = ",".join("?" * len(host_ids))

    port_sql = (
        "SELECT host_id, port, protocol, state, service, version "
        f"FROM ports WHERE host_id IN ({placeholders})"
    )
    cursor = await db.execute(port_sql, host_ids)
    for row in await cursor.fetchall():
        r = dict(row)
        hid = r.pop("host_id")
        hosts_by_id[hid]["ports"].append(r)

    trace_sql = (
        "SELECT host_id, hop, ip, rtt, hostname "
        f"FROM traceroute_hops WHERE host_id IN ({placeholders}) ORDER BY hop"
    )
    cursor = await db.execute(trace_sql, host_ids)
    for row in await cursor.fetchall():
        r = dict(row)
        hid = r.pop("host_id")
        hosts_by_id[hid]["traceroute"].append(r)

    logger.debug("Loaded %d hosts for scan %d", len(hosts_by_id), scan_id)
    return list(hosts_by_id.values())
