from __future__ import annotations

import csv
import io
import json

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from database import get_db, load_scan_hosts

router = APIRouter(prefix="/api/scans/{scan_id}/export", tags=["export"])


@router.get("")
async def export_scan(scan_id: int, format: str = Query("json", pattern="^(json|csv)$")):
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM scans WHERE id=?", (scan_id,))
        scan = await cursor.fetchone()
        if not scan:
            raise HTTPException(404, "Scan not found")

        hosts = await load_scan_hosts(db, scan_id, with_traceroute=False)

        if format == "csv":
            return _export_csv(dict(scan), hosts)
        return _export_json(dict(scan), hosts)
    finally:
        await db.close()


def _export_json(scan: dict, hosts: list[dict]) -> StreamingResponse:
    data = {"scan": scan, "hosts": hosts}
    content = json.dumps(data, indent=2, default=str)
    return StreamingResponse(
        io.BytesIO(content.encode()),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=netvista-scan-{scan['id']}.json"},
    )


def _export_csv(scan: dict, hosts: list[dict]) -> StreamingResponse:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ip", "hostname", "mac", "vendor", "os", "node_type",
        "risk_score", "state", "open_ports",
    ])
    for host in hosts:
        ports_str = ", ".join(
            f"{p['port']}/{p['protocol']}" for p in host.get("ports", [])
        )
        writer.writerow([
            host.get("ip"),
            host.get("hostname"),
            host.get("mac"),
            host.get("vendor"),
            host.get("os_name"),
            host.get("node_type"),
            host.get("risk_score"),
            host.get("state"),
            ports_str,
        ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=netvista-scan-{scan['id']}.csv"},
    )
