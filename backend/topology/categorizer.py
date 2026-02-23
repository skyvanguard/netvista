from __future__ import annotations

from typing import Any

# Port sets for categorization
SERVER_PORTS = {22, 80, 443, 3306, 5432, 8080, 8443, 3000, 8000, 8888, 27017, 6379}
WORKSTATION_PORTS = {3389, 445, 135, 139, 5900, 5800}
NETWORK_DEVICE_PORTS = {161, 23, 179, 830, 8291}  # SNMP, telnet, BGP, NETCONF, MikroTik
PRINTER_PORTS = {9100, 515, 631}  # RAW, LPD, IPP
CAMERA_PORTS = {554, 8000, 8001, 37777}  # RTSP, Hikvision, Dahua
IOT_PORTS = {1883, 8883, 5683}  # MQTT, MQTTS, CoAP

# Vendor keywords
NETWORK_VENDORS = {"cisco", "mikrotik", "fortinet", "fortigate", "juniper", "ubiquiti", "aruba", "tp-link"}
PRINTER_VENDORS = {"hp", "epson", "brother", "canon", "lexmark", "xerox", "ricoh", "kyocera"}
CAMERA_VENDORS = {"hikvision", "dahua", "axis", "hanwha", "vivotek", "uniview"}


def categorize_hosts(hosts: list[dict[str, Any]]) -> None:
    """Assign node_type to each host based on OS, ports, and vendor."""
    for host in hosts:
        host["node_type"] = _categorize_single(host)


def _categorize_single(host: dict[str, Any]) -> str:
    open_ports = {p["port"] for p in host.get("ports", [])}
    os_name = (host.get("os_name") or "").lower()
    vendor = (host.get("vendor") or "").lower()

    # Check vendor first (strongest signal)
    if any(v in vendor for v in CAMERA_VENDORS):
        return "camera"
    if any(v in vendor for v in PRINTER_VENDORS):
        return "printer"
    if any(v in vendor for v in NETWORK_VENDORS):
        return "network_device"

    # Check OS + port patterns
    if open_ports & CAMERA_PORTS and (any(v in os_name for v in CAMERA_VENDORS) or 554 in open_ports):
        return "camera"

    if open_ports & PRINTER_PORTS:
        return "printer"

    if open_ports & NETWORK_DEVICE_PORTS:
        return "network_device"

    if open_ports & IOT_PORTS:
        return "iot"

    if "windows" in os_name and open_ports & WORKSTATION_PORTS:
        return "workstation"

    if open_ports & SERVER_PORTS:
        return "server"

    if "linux" in os_name:
        return "server"

    if "windows" in os_name:
        return "workstation"

    return "unknown"
