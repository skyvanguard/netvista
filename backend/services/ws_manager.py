from __future__ import annotations

import json

from fastapi import WebSocket


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
        dead: list[WebSocket] = []
        for ws in conns:
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                dead.append(ws)
        for ws in dead:
            conns.remove(ws)


ws_manager = WSManager()
