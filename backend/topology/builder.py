from __future__ import annotations

from typing import Any

from topology.subnet import detect_gateways, group_by_subnet


def build_topology(hosts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build topology edges from hosts using traceroute and subnet info."""
    subnets = group_by_subnet(hosts)
    gateways = detect_gateways(hosts)

    edges: list[dict[str, Any]] = []
    seen_edges: set[tuple[str, str]] = set()

    # Tag gateways
    gateway_ips = set(gateways.values())
    for host in hosts:
        if host["ip"] in gateway_ips:
            host["is_gateway"] = True

    # Traceroute edges
    for host in hosts:
        trace = host.get("traceroute", [])
        for i in range(len(trace) - 1):
            src = trace[i].get("ip")
            dst = trace[i + 1].get("ip")
            if src and dst and (src, dst) not in seen_edges:
                seen_edges.add((src, dst))
                edges.append({
                    "source": src,
                    "target": dst,
                    "type": "traceroute",
                    "weight": 1.0,
                })
        # Last hop to host
        if trace:
            last_hop = trace[-1].get("ip")
            if last_hop and last_hop != host["ip"] and (last_hop, host["ip"]) not in seen_edges:
                seen_edges.add((last_hop, host["ip"]))
                edges.append({
                    "source": last_hop,
                    "target": host["ip"],
                    "type": "traceroute",
                    "weight": 1.0,
                })

    # Same-subnet edges: connect hosts to their gateway
    for subnet, subnet_hosts in subnets.items():
        gw = gateways.get(subnet)
        if gw:
            for host in subnet_hosts:
                if host["ip"] != gw and (gw, host["ip"]) not in seen_edges:
                    seen_edges.add((gw, host["ip"]))
                    edges.append({
                        "source": gw,
                        "target": host["ip"],
                        "type": "same_subnet",
                        "weight": 0.5,
                    })

    return edges


def to_cytoscape_elements(
    hosts: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    subnets: dict[str, list[dict[str, Any]]],
    gateways: dict[str, str],
) -> dict[str, list[dict]]:
    """Convert topology data to Cytoscape.js elements format."""
    nodes: list[dict] = []
    edge_elements: list[dict] = []

    # Subnet parent nodes
    for subnet in subnets:
        nodes.append({
            "data": {
                "id": f"subnet-{subnet}",
                "label": subnet,
                "type": "subnet",
                "hostCount": len(subnets[subnet]),
                "gateway": gateways.get(subnet),
            },
        })

    # Host nodes
    gateway_ips = set(gateways.values())
    for host in hosts:
        node_data: dict[str, Any] = {
            "id": host["ip"],
            "label": host.get("hostname") or host["ip"],
            "ip": host["ip"],
            "type": host.get("node_type", "unknown"),
            "os": host.get("os_name"),
            "vendor": host.get("vendor"),
            "riskScore": host.get("risk_score", 0),
            "portCount": len(host.get("ports", [])),
            "isGateway": host["ip"] in gateway_ips,
            "parent": f"subnet-{host.get('subnet', 'unknown')}",
        }
        nodes.append({"data": node_data})

    # Edges
    for edge in edges:
        edge_elements.append({
            "data": {
                "id": f"{edge['source']}->{edge['target']}",
                "source": edge["source"],
                "target": edge["target"],
                "type": edge.get("type", "traceroute"),
                "weight": edge.get("weight", 1.0),
            },
        })

    return {"nodes": nodes, "edges": edge_elements}
