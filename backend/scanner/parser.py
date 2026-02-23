from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any


def parse_nmap_xml(xml_path: str) -> list[dict[str, Any]]:
    """Parse nmap XML output into a list of host dicts."""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    hosts: list[dict[str, Any]] = []

    for host_el in root.findall("host"):
        host = _parse_host(host_el)
        if host:
            hosts.append(host)

    return hosts


def _parse_host(host_el: ET.Element) -> dict[str, Any] | None:
    status = host_el.find("status")
    if status is None or status.get("state") != "up":
        return None

    host: dict[str, Any] = {"state": "up", "ports": [], "traceroute": []}

    # IP address
    for addr in host_el.findall("address"):
        if addr.get("addrtype") == "ipv4":
            host["ip"] = addr.get("addr", "")
        elif addr.get("addrtype") == "mac":
            host["mac"] = addr.get("addr", "")
            host["vendor"] = addr.get("vendor", "")

    if "ip" not in host:
        return None

    # Hostname
    hostnames = host_el.find("hostnames")
    if hostnames is not None:
        hn = hostnames.find("hostname")
        if hn is not None:
            host["hostname"] = hn.get("name", "")

    # OS detection
    os_el = host_el.find("os")
    if os_el is not None:
        osmatch = os_el.find("osmatch")
        if osmatch is not None:
            host["os_name"] = osmatch.get("name", "")
            host["os_accuracy"] = int(osmatch.get("accuracy", "0"))

    # Ports
    ports_el = host_el.find("ports")
    if ports_el is not None:
        for port_el in ports_el.findall("port"):
            port = _parse_port(port_el)
            if port:
                host["ports"].append(port)

    # Traceroute
    trace_el = host_el.find("trace")
    if trace_el is not None:
        for hop_el in trace_el.findall("hop"):
            hop = {
                "hop": int(hop_el.get("ttl", "0")),
                "ip": hop_el.get("ipaddr", ""),
                "rtt": float(hop_el.get("rtt", "0")),
                "hostname": hop_el.get("host", ""),
            }
            host["traceroute"].append(hop)

    return host


def _parse_port(port_el: ET.Element) -> dict[str, Any] | None:
    state_el = port_el.find("state")
    if state_el is None or state_el.get("state") != "open":
        return None

    port: dict[str, Any] = {
        "port": int(port_el.get("portid", "0")),
        "protocol": port_el.get("protocol", "tcp"),
        "state": "open",
    }

    service_el = port_el.find("service")
    if service_el is not None:
        port["service"] = service_el.get("name", "")
        version_parts = []
        if service_el.get("product"):
            version_parts.append(service_el.get("product", ""))
        if service_el.get("version"):
            version_parts.append(service_el.get("version", ""))
        if version_parts:
            port["version"] = " ".join(version_parts)

    return port
