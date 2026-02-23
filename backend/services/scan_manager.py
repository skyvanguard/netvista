from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from database import get_db
from scanner.nmap_runner import run_nmap_scan
from services.ws_manager import ws_manager
from topology.builder import build_topology
from topology.categorizer import categorize_hosts
from topology.risk import score_hosts


async def execute_scan(scan_id: int, target: str, profile: str) -> None:
    """Run scan in background, store results, compute topology."""
    db = await get_db()
    try:
        now = datetime.now(timezone.utc).isoformat()
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
                "hosts_found": 0,
            })

        try:
            hosts = await run_nmap_scan(target, profile, on_progress)
        except Exception as exc:
            now = datetime.now(timezone.utc).isoformat()
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
                "hosts_found": 0,
            })
            return

        # Categorize and score
        categorize_hosts(hosts)
        score_hosts(hosts)

        # Store hosts
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

            for port in host.get("ports", []):
                await db.execute(
                    """INSERT INTO ports (host_id, port, protocol, state, service, version)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (host_id, port["port"], port["protocol"], port["state"],
                     port.get("service"), port.get("version")),
                )

            for hop in host.get("traceroute", []):
                await db.execute(
                    """INSERT INTO traceroute_hops (host_id, hop, ip, rtt, hostname)
                       VALUES (?, ?, ?, ?, ?)""",
                    (host_id, hop["hop"], hop.get("ip"), hop.get("rtt"),
                     hop.get("hostname")),
                )

        # Build topology edges
        edges = build_topology(hosts)
        for edge in edges:
            await db.execute(
                """INSERT INTO topology_edges (scan_id, source_ip, target_ip, edge_type, weight)
                   VALUES (?, ?, ?, ?, ?)""",
                (scan_id, edge["source"], edge["target"],
                 edge.get("type", "traceroute"), edge.get("weight", 1.0)),
            )

        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "UPDATE scans SET status='completed', finished_at=?, host_count=? WHERE id=?",
            (now, len(hosts), scan_id),
        )
        await db.commit()

        await ws_manager.broadcast(scan_id, {
            "scan_id": scan_id,
            "status": "completed",
            "progress": 1.0,
            "message": f"Scan complete — {len(hosts)} hosts",
            "hosts_found": len(hosts),
        })

    except Exception as exc:
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "UPDATE scans SET status='failed', finished_at=?, error=? WHERE id=?",
            (now, str(exc), scan_id),
        )
        await db.commit()
    finally:
        await db.close()
