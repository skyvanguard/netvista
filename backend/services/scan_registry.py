from __future__ import annotations

import asyncio

# Tracks the background asyncio.Task for each in-flight scan so a DELETE can
# cancel a scan that is still running. Single-process only (matches the
# single-worker assumption of ws_manager).
_tasks: dict[int, asyncio.Task] = {}


def register(scan_id: int, task: asyncio.Task) -> None:
    """Register a running scan task; it deregisters itself when done."""
    _tasks[scan_id] = task
    task.add_done_callback(lambda _: _tasks.pop(scan_id, None))


def cancel(scan_id: int) -> bool:
    """Cancel a running scan task if present. Returns True if a task was cancelled."""
    task = _tasks.get(scan_id)
    if task and not task.done():
        task.cancel()
        return True
    return False
