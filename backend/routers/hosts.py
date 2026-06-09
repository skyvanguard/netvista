from __future__ import annotations

import json
from fastapi import APIRouter, HTTPException

from database import get_db, load_scan_hosts
from models import HostOut

router = APIRouter(prefix="/api/scans/{scan_id}/hosts", tags=["hosts"])


@router.get("", response_model=list[HostOut])
async def list_hosts(scan_id: int) -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT id FROM scans WHERE id=?", (scan_id,))
        if not await cursor.fetchone():
            raise HTTPException(404, "Scan not found")

        return await load_scan_hosts(db, scan_id)
    finally:
        await db.close()


@router.get("/{ip}", response_model=HostOut)
async def get_host(scan_id: int, ip: str) -> dict:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM hosts WHERE scan_id=? AND ip=?", (scan_id, ip),
        )
        host = await cursor.fetchone()
        if not host:
            raise HTTPException(404, "Host not found")

        host = dict(host)

        cursor = await db.execute(
            "SELECT port, protocol, state, service, version FROM ports WHERE host_id=?",
            (host["id"],),
        )
        host["ports"] = [dict(r) for r in await cursor.fetchall()]

        cursor = await db.execute(
            "SELECT hop, ip, rtt, hostname FROM traceroute_hops WHERE host_id=? ORDER BY hop",
            (host["id"],),
        )
        host["traceroute"] = [dict(r) for r in await cursor.fetchall()]

        return host
    finally:
        await db.close()
