from __future__ import annotations

import asyncio
import json
import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WSManager:
    """Manages WebSocket connections per scan for real-time progress."""

    def __init__(self) -> None:
        self._connections: dict[int, list[WebSocket]] = {}

    async def connect(self, scan_id: int, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.setdefault(scan_id, []).append(ws)

    def disconnect(self, scan_id: int, ws: WebSocket) -> None:
        conns = self._connections.get(scan_id, [])
        if ws in conns:
            conns.remove(ws)

    async def broadcast(self, scan_id: int, data: dict) -> None:
        conns = self._connections.get(scan_id, [])
        if not conns:
            return
        payload = json.dumps(data)
        results = await asyncio.gather(
            *[ws.send_text(payload) for ws in conns],
            return_exceptions=True,
        )
        dead = [
            ws for ws, result in zip(conns, results, strict=True)
            if isinstance(result, Exception)
        ]
        for ws in dead:
            logger.warning("Removing dead WebSocket for scan %d", scan_id)
            conns.remove(ws)


ws_manager = WSManager()
