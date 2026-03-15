from __future__ import annotations

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from database import get_db_dep
from models import SubnetOut, TopologyOut
from services.host_loader import load_hosts_with_data
from topology.builder import to_cytoscape_elements
from topology.subnet import detect_gateways, group_by_subnet

router = APIRouter(prefix="/api/scans/{scan_id}", tags=["topology"])


@router.get("/topology", response_model=TopologyOut)
async def get_topology(scan_id: int, db: aiosqlite.Connection = Depends(get_db_dep)) -> dict:
    cursor = await db.execute("SELECT id FROM scans WHERE id=?", (scan_id,))
    if not await cursor.fetchone():
        raise HTTPException(404, "Scan not found")

    hosts = await load_hosts_with_data(db, scan_id)

    # Load edges
    cursor = await db.execute(
        "SELECT source_ip, target_ip, edge_type, weight FROM topology_edges WHERE scan_id=?",
        (scan_id,),
    )
    edges = [
        {"source": r["source_ip"], "target": r["target_ip"],
         "type": r["edge_type"], "weight": r["weight"]}
        for r in await cursor.fetchall()
    ]

    subnets = group_by_subnet(hosts)
    gateways = detect_gateways(hosts)
    elements = to_cytoscape_elements(hosts, edges, subnets, gateways)

    return elements


@router.get("/subnets", response_model=list[SubnetOut])
async def get_subnets(scan_id: int, db: aiosqlite.Connection = Depends(get_db_dep)) -> list[dict]:
    cursor = await db.execute("SELECT id FROM scans WHERE id=?", (scan_id,))
    if not await cursor.fetchone():
        raise HTTPException(404, "Scan not found")

    hosts = await load_hosts_with_data(db, scan_id)
    subnets = group_by_subnet(hosts)
    gateways = detect_gateways(hosts)

    result = []
    for subnet, subnet_hosts in subnets.items():
        result.append({
            "subnet": subnet,
            "gateway": gateways.get(subnet),
            "host_count": len(subnet_hosts),
            "hosts": [h["ip"] for h in subnet_hosts],
        })

    return result
