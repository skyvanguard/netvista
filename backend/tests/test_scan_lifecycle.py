from __future__ import annotations

import asyncio

import database
from database import init_db, get_db
from services.scan_manager import fail_orphaned_scans
from services.scan_registry import register, cancel


def _use_temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DATABASE_URL", str(tmp_path / "test.db"))


def test_fail_orphaned_scans_marks_only_non_terminal(tmp_path, monkeypatch):
    _use_temp_db(tmp_path, monkeypatch)

    async def scenario():
        await init_db()
        db = await get_db()
        for status in ("running", "pending", "completed", "failed"):
            await db.execute(
                "INSERT INTO scans (target, profile, status, created_at) "
                "VALUES (?, 'quick', ?, 'now')",
                (f"t-{status}", status),
            )
        await db.commit()
        await db.close()

        await fail_orphaned_scans()

        db = await get_db()
        cur = await db.execute("SELECT status, error FROM scans ORDER BY id")
        rows = [(r["status"], r["error"]) for r in await cur.fetchall()]
        await db.close()
        return rows

    rows = asyncio.run(scenario())
    assert rows[0][0] == "failed" and "restart" in rows[0][1].lower()  # was running
    assert rows[1][0] == "failed"                                       # was pending
    assert rows[2] == ("completed", None)                              # untouched
    assert rows[3][0] == "failed"                                       # already failed


def test_registry_cancels_running_task():
    async def scenario():
        started = asyncio.Event()

        async def never_ending():
            started.set()
            await asyncio.Event().wait()

        task = asyncio.create_task(never_ending())
        register(7, task)
        await started.wait()

        assert cancel(7) is True
        try:
            await task
        except asyncio.CancelledError:
            pass
        assert task.cancelled()
        # The done callback (scheduled via call_soon) deregisters the task;
        # yield once so it runs before we re-check.
        await asyncio.sleep(0)
        assert cancel(7) is False

    asyncio.run(scenario())
