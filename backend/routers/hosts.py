from __future__ import annotations

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from database import get_db_dep
from models import HostOut
from services.host_loader import load_hosts_with_data

router = APIRouter(prefix="/api/scans/{scan_id}/hosts", tags=["hosts"])


@router.get("", response_model=list[HostOut])
async def list_hosts(scan_id: int, db: aiosqlite.Connection = Depends(get_db_dep)) -> list[dict]:
    cursor = await db.execute("SELECT id FROM scans WHERE id=?", (scan_id,))
    if not await cursor.fetchone():
        raise HTTPException(404, "Scan not found")

    return await load_hosts_with_data(db, scan_id)


@router.get("/{ip}", response_model=HostOut)
async def get_host(scan_id: int, ip: str, db: aiosqlite.Connection = Depends(get_db_dep)) -> dict:
    cursor = await db.execute(
        "SELECT * FROM hosts WHERE scan_id=? AND ip=?", (scan_id, ip),
    )
    host = await cursor.fetchone()
    if not host:
        raise HTTPException(404, "Host not found")

    host = dict(host)
    host_id = host["id"]

    cursor = await db.execute(
        "SELECT port, protocol, state, service, version FROM ports WHERE host_id=?",
        (host_id,),
    )
    host["ports"] = [dict(r) for r in await cursor.fetchall()]

    cursor = await db.execute(
        "SELECT hop, ip, rtt, hostname FROM traceroute_hops WHERE host_id=? ORDER BY hop",
        (host_id,),
    )
    host["traceroute"] = [dict(r) for r in await cursor.fetchall()]

    return host
