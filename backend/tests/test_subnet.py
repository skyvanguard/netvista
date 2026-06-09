from __future__ import annotations

from topology.subnet import group_by_subnet, detect_gateways


def test_group_by_subnet_groups_and_tags_hosts():
    hosts = [
        {"ip": "192.168.1.10"},
        {"ip": "192.168.1.20"},
        {"ip": "10.0.0.5"},
    ]
    subnets = group_by_subnet(hosts)
    assert set(subnets) == {"192.168.1.0/24", "10.0.0.0/24"}
    assert len(subnets["192.168.1.0/24"]) == 2
    # group_by_subnet mutates each host with its /24 key (relied on downstream).
    assert hosts[0]["subnet"] == "192.168.1.0/24"


def test_invalid_ip_falls_back_to_unknown():
    hosts = [{"ip": "not-an-ip"}]
    subnets = group_by_subnet(hosts)
    assert "unknown" in subnets
    assert hosts[0]["subnet"] == "unknown"


def test_detect_gateways_picks_most_common_penultimate_hop():
    hosts = [
        {
            "ip": "192.168.1.10",
            "traceroute": [
                {"ip": "192.168.1.1"},
                {"ip": "192.168.1.10"},
            ],
        },
        {
            "ip": "192.168.1.11",
            "traceroute": [
                {"ip": "192.168.1.1"},
                {"ip": "192.168.1.11"},
            ],
        },
    ]
    group_by_subnet(hosts)  # sets host["subnet"], required by detect_gateways
    gateways = detect_gateways(hosts)
    assert gateways["192.168.1.0/24"] == "192.168.1.1"


def test_no_gateway_when_traceroute_too_short():
    hosts = [{"ip": "192.168.1.10", "traceroute": [{"ip": "192.168.1.10"}]}]
    group_by_subnet(hosts)
    assert detect_gateways(hosts) == {}
