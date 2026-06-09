from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)

from auth import verify_api_key
from config import API_KEY
from database import get_db
from models import ScanCreate, ScanOut
from services.scan_manager import execute_scan
from services.scan_registry import cancel, register
from services.ws_manager import ws_manager

router = APIRouter(prefix="/api/scans", tags=["scans"])

# Applied per-endpoint (not at router level) so the WebSocket below can
# authenticate via query param instead of a header.
_auth = [Depends(verify_api_key)]


@router.post("", response_model=ScanOut, status_code=201, dependencies=_auth)
async def create_scan(body: ScanCreate) -> dict:
    db = await get_db()
    try:
        now = datetime.now(UTC).isoformat()
        cursor = await db.execute(
            "INSERT INTO scans (target, profile, status, created_at) VALUES (?, ?, 'pending', ?)",
            (body.target, body.profile, now),
        )
        scan_id = cursor.lastrowid
        await db.commit()

        row = await db.execute("SELECT * FROM scans WHERE id=?", (scan_id,))
        scan = await row.fetchone()

        # Launch background scan and track it so it can be cancelled.
        task = asyncio.create_task(execute_scan(scan_id, body.target, body.profile))
        register(scan_id, task)

        return dict(scan)
    finally:
        await db.close()


@router.get("", response_model=list[ScanOut], dependencies=_auth)
async def list_scans() -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM scans ORDER BY id DESC")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


@router.get("/{scan_id}", response_model=ScanOut, dependencies=_auth)
async def get_scan(scan_id: int) -> dict:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM scans WHERE id=?", (scan_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(404, "Scan not found")
        return dict(row)
    finally:
        await db.close()


@router.delete("/{scan_id}", status_code=204, dependencies=_auth)
async def delete_scan(scan_id: int) -> None:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT id FROM scans WHERE id=?", (scan_id,))
        if not await cursor.fetchone():
            raise HTTPException(404, "Scan not found")
        # Stop the background task (and its nmap subprocess) if still running.
        cancel(scan_id)
        await db.execute("DELETE FROM scans WHERE id=?", (scan_id,))
        await db.commit()
    finally:
        await db.close()


@router.websocket("/{scan_id}/ws")
async def scan_ws(
    websocket: WebSocket,
    scan_id: int,
    api_key: str | None = Query(default=None),
) -> None:
    # Browsers can't set custom headers on a WebSocket, so the key (when auth
    # is enabled) is passed as a query param. Reject before accepting.
    if API_KEY and api_key != API_KEY:
        await websocket.close(code=1008)  # policy violation
        return
    await ws_manager.connect(scan_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(scan_id, websocket)
