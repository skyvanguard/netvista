from __future__ import annotations

import asyncio

import database
import services.scan_manager as scan_manager
from database import get_db, init_db, load_scan_hosts
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


def test_execute_scan_respects_concurrency_limit(tmp_path, monkeypatch):
    _use_temp_db(tmp_path, monkeypatch)
    # Force a limit of 1 regardless of the configured default.
    monkeypatch.setattr(scan_manager, "_scan_semaphore", asyncio.Semaphore(1))

    async def scenario():
        await init_db()
        db = await get_db()
        for i in (1, 2, 3):
            await db.execute(
                "INSERT INTO scans (id, target, profile, status, created_at) "
                "VALUES (?, '10.0.0.1', 'quick', 'pending', 'now')",
                (i,),
            )
        await db.commit()
        await db.close()

        in_flight = 0
        peak = 0

        async def fake_nmap(target, profile, on_progress=None):
            nonlocal in_flight, peak
            in_flight += 1
            peak = max(peak, in_flight)
            await asyncio.sleep(0.02)
            in_flight -= 1
            return []

        monkeypatch.setattr(scan_manager, "run_nmap_scan", fake_nmap)

        await asyncio.gather(
            *(scan_manager.execute_scan(i, "10.0.0.1", "quick") for i in (1, 2, 3))
        )
        return peak

    peak = asyncio.run(scenario())
    assert peak == 1  # never more than the semaphore allows


def test_execute_scan_persists_hosts_ports_and_edges(tmp_path, monkeypatch):
    _use_temp_db(tmp_path, monkeypatch)

    fake_hosts = [
        {
            "ip": "192.168.1.10",
            "ports": [
                {"port": 22, "protocol": "tcp", "state": "open", "service": "ssh", "version": None},
                {"port": 80, "protocol": "tcp", "state": "open", "service": "http", "version": None},
            ],
            "traceroute": [
                {"hop": 1, "ip": "192.168.1.1", "rtt": 1.0, "hostname": None},
                {"hop": 2, "ip": "192.168.1.10", "rtt": 2.0, "hostname": None},
            ],
        },
        {
            "ip": "192.168.1.20",
            "ports": [
                {"port": 443, "protocol": "tcp", "state": "open", "service": "https", "version": None},
            ],
            "traceroute": [
                {"hop": 1, "ip": "192.168.1.1", "rtt": 1.0, "hostname": None},
                {"hop": 2, "ip": "192.168.1.20", "rtt": 2.0, "hostname": None},
            ],
        },
    ]

    async def scenario():
        await init_db()
        db = await get_db()
        await db.execute(
            "INSERT INTO scans (id, target, profile, status, created_at) "
            "VALUES (1, '192.168.1.0/24', 'standard', 'pending', 'now')"
        )
        await db.commit()
        await db.close()

        async def fake_nmap(target, profile, on_progress=None):
            return [dict(h) for h in fake_hosts]

        monkeypatch.setattr(scan_manager, "run_nmap_scan", fake_nmap)
        await scan_manager.execute_scan(1, "192.168.1.0/24", "standard")

        db = await get_db()
        cur = await db.execute("SELECT status, host_count FROM scans WHERE id=1")
        scan = dict(await cur.fetchone())
        hosts = await load_scan_hosts(db, 1)
        cur = await db.execute("SELECT COUNT(*) AS n FROM topology_edges WHERE scan_id=1")
        edge_count = (await cur.fetchone())["n"]
        await db.close()
        return scan, hosts, edge_count

    scan, hosts, edge_count = asyncio.run(scenario())
    assert scan["status"] == "completed"
    assert scan["host_count"] == 2
    by_ip = {h["ip"]: h for h in hosts}
    assert {p["port"] for p in by_ip["192.168.1.10"]["ports"]} == {22, 80}
    assert {p["port"] for p in by_ip["192.168.1.20"]["ports"]} == {443}
    assert [h["hop"] for h in by_ip["192.168.1.10"]["traceroute"]] == [1, 2]
    assert edge_count > 0  # traceroute + same-subnet edges were batch-inserted


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
