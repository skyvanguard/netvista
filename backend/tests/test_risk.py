from __future__ import annotations

import json

from topology.risk import score_hosts, _score_single, MAX_RISK


def host(*ports):
    return {"ports": [{"port": p} for p in ports]}


def test_no_risky_ports_scores_zero():
    score, details = _score_single(host(80, 443))
    assert score == 0.0
    assert details == []


def test_single_risky_port():
    score, details = _score_single(host(23))  # Telnet = 3.0
    assert score == 3.0
    assert len(details) == 1
    assert "Telnet" in details[0]


def test_scores_are_additive():
    # FTP (2.0) + SMB (2.0) + RDP (2.0) = 6.0
    score, _ = _score_single(host(21, 445, 3389))
    assert score == 6.0


def test_score_is_capped_at_max():
    # Many high-risk ports would exceed 10 without the cap.
    score, _ = _score_single(host(23, 512, 513, 514, 6379, 27017, 11211))
    assert score == MAX_RISK


def test_large_attack_surface_bonus():
    ports = list(range(40000, 40025))  # 25 non-risky ports -> >20 triggers +1.0
    score, details = _score_single(host(*ports))
    assert score == 1.0
    assert any("attack surface" in d for d in details)


def test_score_hosts_serialises_details_as_json():
    hosts = [host(23), host(80)]
    score_hosts(hosts)
    assert hosts[0]["risk_score"] == 3.0
    assert json.loads(hosts[0]["risk_details"])[0].startswith("Port 23")
    # No risky ports -> details stored as None, not an empty JSON array.
    assert hosts[1]["risk_score"] == 0.0
    assert hosts[1]["risk_details"] is None
