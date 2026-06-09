from __future__ import annotations

import asyncio

import database
from database import init_db, get_db, load_scan_hosts


def _use_temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DATABASE_URL", str(tmp_path / "test.db"))


async def _seed(db):
    """Two scans; scan 1 has two hosts with ports + traceroute, scan 2 one host."""
    await db.execute(
        "INSERT INTO scans (id, target, profile, status, created_at) "
        "VALUES (1, 'a', 'quick', 'completed', 'now'), "
        "       (2, 'b', 'quick', 'completed', 'now')"
    )
    await db.execute(
        "INSERT INTO hosts (id, scan_id, ip) VALUES "
        "(10, 1, '192.168.1.10'), (11, 1, '192.168.1.11'), (20, 2, '10.0.0.5')"
    )
    await db.execute(
        "INSERT INTO ports (host_id, port, protocol, state, service) VALUES "
        "(10, 22, 'tcp', 'open', 'ssh'), "
        "(10, 80, 'tcp', 'open', 'http'), "
        "(11, 443, 'tcp', 'open', 'https'), "
        "(20, 53, 'udp', 'open', 'domain')"
    )
    await db.execute(
        "INSERT INTO traceroute_hops (host_id, hop, ip) VALUES "
        "(10, 2, '192.168.1.10'), (10, 1, '192.168.1.1')"
    )
    await db.commit()


def test_load_scan_hosts_groups_children_per_host(tmp_path, monkeypatch):
    _use_temp_db(tmp_path, monkeypatch)

    async def scenario():
        await init_db()
        db = await get_db()
        await _seed(db)
        hosts = await load_scan_hosts(db, 1)
        await db.close()
        return hosts

    hosts = asyncio.run(scenario())
    # Scan 2's host must not leak in.
    assert {h["ip"] for h in hosts} == {"192.168.1.10", "192.168.1.11"}
    by_ip = {h["ip"]: h for h in hosts}
    assert {p["port"] for p in by_ip["192.168.1.10"]["ports"]} == {22, 80}
    assert {p["port"] for p in by_ip["192.168.1.11"]["ports"]} == {443}
    # Hops come back ordered by hop number.
    assert [h["hop"] for h in by_ip["192.168.1.10"]["traceroute"]] == [1, 2]


def test_load_scan_hosts_can_skip_traceroute(tmp_path, monkeypatch):
    _use_temp_db(tmp_path, monkeypatch)

    async def scenario():
        await init_db()
        db = await get_db()
        await _seed(db)
        hosts = await load_scan_hosts(db, 1, with_traceroute=False)
        await db.close()
        return hosts

    hosts = asyncio.run(scenario())
    assert all("traceroute" not in h for h in hosts)
    assert all("ports" in h for h in hosts)


def test_load_scan_hosts_empty_scan(tmp_path, monkeypatch):
    _use_temp_db(tmp_path, monkeypatch)

    async def scenario():
        await init_db()
        db = await get_db()
        hosts = await load_scan_hosts(db, 999)
        await db.close()
        return hosts

    assert asyncio.run(scenario()) == []
