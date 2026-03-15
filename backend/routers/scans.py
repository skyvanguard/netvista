from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi import Query as QueryParam
from fastapi.responses import Response

from database import get_db_dep
from models import PaginatedScans, ScanCreate, ScanOut
from services.scan_manager import execute_scan
from services.ws_manager import ws_manager

router = APIRouter(prefix="/api/scans", tags=["scans"])

_scan_semaphore = asyncio.Semaphore(3)


@router.post("", response_model=ScanOut, status_code=201)
async def create_scan(body: ScanCreate, db: aiosqlite.Connection = Depends(get_db_dep)) -> dict:
    if _scan_semaphore.locked():
        raise HTTPException(429, "Too many concurrent scans. Please wait.")

    now = datetime.now(UTC).isoformat()
    cursor = await db.execute(
        "INSERT INTO scans (target, profile, status, created_at) VALUES (?, ?, 'pending', ?)",
        (body.target, body.profile, now),
    )
    scan_id = cursor.lastrowid
    await db.commit()

    row = await db.execute("SELECT * FROM scans WHERE id=?", (scan_id,))
    scan = await row.fetchone()

    # Launch background scan
    asyncio.create_task(execute_scan(scan_id, body.target, body.profile))

    return dict(scan)


@router.get("", response_model=PaginatedScans)
async def list_scans(
    skip: int = QueryParam(0, ge=0),
    limit: int = QueryParam(50, ge=1, le=200),
    db: aiosqlite.Connection = Depends(get_db_dep),
) -> dict:
    cursor = await db.execute("SELECT COUNT(*) as cnt FROM scans")
    row = await cursor.fetchone()
    total = row["cnt"]

    cursor = await db.execute(
        "SELECT * FROM scans ORDER BY id DESC LIMIT ? OFFSET ?",
        (limit, skip),
    )
    rows = await cursor.fetchall()
    return {
        "items": [dict(r) for r in rows],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/{scan_id}", response_model=ScanOut)
async def get_scan(scan_id: int, db: aiosqlite.Connection = Depends(get_db_dep)) -> dict:
    cursor = await db.execute("SELECT * FROM scans WHERE id=?", (scan_id,))
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(404, "Scan not found")
    return dict(row)


@router.delete("/{scan_id}", status_code=204, response_class=Response, response_model=None)
async def delete_scan(scan_id: int, db: aiosqlite.Connection = Depends(get_db_dep)):
    cursor = await db.execute("SELECT id FROM scans WHERE id=?", (scan_id,))
    if not await cursor.fetchone():
        raise HTTPException(404, "Scan not found")
    await db.execute("DELETE FROM scans WHERE id=?", (scan_id,))
    await db.commit()


@router.websocket("/{scan_id}/ws")
async def scan_ws(websocket: WebSocket, scan_id: int) -> None:
    await ws_manager.connect(scan_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(scan_id, websocket)
