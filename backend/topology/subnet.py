from __future__ import annotations

import ipaddress
from collections import defaultdict
from typing import Any


def group_by_subnet(hosts: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Group hosts by their /24 subnet."""
    subnets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for host in hosts:
        ip = host.get("ip", "")
        try:
            network = ipaddress.ip_network(f"{ip}/24", strict=False)
            subnet_key = str(network)
        except ValueError:
            subnet_key = "unknown"
        host["subnet"] = subnet_key
        subnets[subnet_key].append(host)
    return dict(subnets)


def detect_gateways(hosts: list[dict[str, Any]]) -> dict[str, str]:
    """Detect gateway for each subnet using traceroute penultimate hop."""
    # Collect penultimate hops per subnet
    subnet_hops: dict[str, list[str]] = defaultdict(list)

    for host in hosts:
        subnet = host.get("subnet", "unknown")
        trace = host.get("traceroute", [])
        if len(trace) >= 2:
            # Penultimate hop is likely the gateway
            penultimate = trace[-2]
            if penultimate.get("ip"):
                subnet_hops[subnet].append(penultimate["ip"])

    # Most common penultimate hop per subnet = gateway
    gateways: dict[str, str] = {}
    for subnet, hops in subnet_hops.items():
        if hops:
            from collections import Counter
            counter = Counter(hops)
            gateways[subnet] = counter.most_common(1)[0][0]

    return gateways
