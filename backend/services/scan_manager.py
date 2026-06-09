from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime

from config import MAX_CONCURRENT_SCANS
from database import get_db
from scanner.nmap_runner import run_nmap_scan
from services.ws_manager import ws_manager
from topology.builder import build_topology
from topology.categorizer import categorize_hosts
from topology.risk import score_hosts

log = logging.getLogger("netvista.scan")

# Bound how many nmap scans run at once; extras stay 'pending' until a slot
# frees up, so a burst of deep scans can't saturate the host.
_scan_semaphore = asyncio.Semaphore(MAX_CONCURRENT_SCANS)


async def fail_orphaned_scans() -> None:
    """Mark scans left 'running'/'pending' by a previous process as failed.

    Background scan tasks do not survive a server restart, so any scan still
    in a non-terminal state at startup is dead and must not stay stuck.
    """
    db = await get_db()
    try:
        now = datetime.now(UTC).isoformat()
        cursor = await db.execute(
            "UPDATE scans SET status='failed', finished_at=?, error=? "
            "WHERE status IN ('pending', 'running')",
            (now, "Interrupted by server restart"),
        )
        await db.commit()
        if cursor.rowcount:
            log.warning("Marked %d orphaned scan(s) as failed on startup", cursor.rowcount)
    finally:
        await db.close()


async def execute_scan(scan_id: int, target: str, profile: str) -> None:
    """Wait for a free concurrency slot, then run the scan.

    While queued the scan stays 'pending' (its DB row is untouched until a
    slot is acquired).
    """
    async with _scan_semaphore:
        await _execute_scan(scan_id, target, profile)


async def _execute_scan(scan_id: int, target: str, profile: str) -> None:
    """Run scan in background, store results, compute topology."""
    db = await get_db()
    try:
        log.info("Scan %d starting: target=%s profile=%s", scan_id, target, profile)
        now = datetime.now(UTC).isoformat()
        await db.execute(
            "UPDATE scans SET status='running', started_at=? WHERE id=?",
            (now, scan_id),
        )
        await db.commit()

        async def on_progress(pct: float, msg: str) -> None:
            await ws_manager.broadcast(scan_id, {
                "scan_id": scan_id,
                "status": "running",
                "progress": round(pct, 3),
                "message": msg,
                # Unknown until the scan finishes; don't claim 0.
                "hosts_found": None,
            })

        try:
            hosts = await run_nmap_scan(target, profile, on_progress)
        except Exception as exc:
            log.exception("Scan %d failed during nmap run", scan_id)
            now = datetime.now(UTC).isoformat()
            await db.execute(
                "UPDATE scans SET status='failed', finished_at=?, error=? WHERE id=?",
                (now, str(exc), scan_id),
            )
            await db.commit()
            await ws_manager.broadcast(scan_id, {
                "scan_id": scan_id,
                "status": "failed",
                "progress": 0,
                "message": str(exc),
                "hosts_found": None,
            })
            return

        # Categorize and score
        categorize_hosts(hosts)
        score_hosts(hosts)

        # Store hosts (one INSERT per host to get its id, then batch its
        # ports/traceroute hops via executemany to cut round-trips).
        for host in hosts:
            cursor = await db.execute(
                """INSERT INTO hosts (scan_id, ip, hostname, mac, vendor,
                   os_name, os_accuracy, state, node_type, risk_score, risk_details)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    scan_id,
                    host["ip"],
                    host.get("hostname"),
                    host.get("mac"),
                    host.get("vendor"),
                    host.get("os_name"),
                    host.get("os_accuracy"),
                    host.get("state", "up"),
                    host.get("node_type", "unknown"),
                    host.get("risk_score", 0),
                    host.get("risk_details"),
                ),
            )
            host_id = cursor.lastrowid

            ports = host.get("ports", [])
            if ports:
                await db.executemany(
                    """INSERT INTO ports (host_id, port, protocol, state, service, version)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    [
                        (host_id, p["port"], p["protocol"], p["state"],
                         p.get("service"), p.get("version"))
                        for p in ports
                    ],
                )

            hops = host.get("traceroute", [])
            if hops:
                await db.executemany(
                    """INSERT INTO traceroute_hops (host_id, hop, ip, rtt, hostname)
                       VALUES (?, ?, ?, ?, ?)""",
                    [
                        (host_id, h["hop"], h.get("ip"), h.get("rtt"), h.get("hostname"))
                        for h in hops
                    ],
                )

        # Build topology edges
        edges = build_topology(hosts)
        if edges:
            await db.executemany(
                """INSERT INTO topology_edges (scan_id, source_ip, target_ip, edge_type, weight)
                   VALUES (?, ?, ?, ?, ?)""",
                [
                    (scan_id, e["source"], e["target"],
                     e.get("type", "traceroute"), e.get("weight", 1.0))
                    for e in edges
                ],
            )

        now = datetime.now(UTC).isoformat()
        await db.execute(
            "UPDATE scans SET status='completed', finished_at=?, host_count=? WHERE id=?",
            (now, len(hosts), scan_id),
        )
        await db.commit()
        log.info("Scan %d completed: %d hosts, %d edges", scan_id, len(hosts), len(edges))

        await ws_manager.broadcast(scan_id, {
            "scan_id": scan_id,
            "status": "completed",
            "progress": 1.0,
            "message": f"Scan complete — {len(hosts)} hosts",
            "hosts_found": len(hosts),
        })

    except Exception as exc:
        log.exception("Scan %d failed while storing results", scan_id)
        now = datetime.now(UTC).isoformat()
        await db.execute(
            "UPDATE scans SET status='failed', finished_at=?, error=? WHERE id=?",
            (now, str(exc), scan_id),
        )
        await db.commit()
    finally:
        await db.close()
