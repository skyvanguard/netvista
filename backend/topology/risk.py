from __future__ import annotations

import json
from typing import Any

# Dangerous ports and their risk contribution
RISKY_PORTS: dict[int, tuple[float, str]] = {
    21: (2.0, "FTP — cleartext authentication"),
    23: (3.0, "Telnet — cleartext protocol"),
    25: (1.0, "SMTP — potential open relay"),
    69: (1.5, "TFTP — no authentication"),
    111: (1.5, "RPCbind — information leak"),
    135: (1.0, "MSRPC — Windows RPC"),
    139: (1.5, "NetBIOS — SMB v1 risk"),
    445: (2.0, "SMB — ransomware vector"),
    512: (2.5, "rexec — remote execution"),
    513: (2.5, "rlogin — remote login"),
    514: (2.5, "rsh — remote shell"),
    1433: (1.5, "MSSQL — database exposed"),
    1521: (1.5, "Oracle DB — database exposed"),
    2049: (2.0, "NFS — file share exposed"),
    3306: (1.5, "MySQL — database exposed"),
    3389: (2.0, "RDP — brute force target"),
    5432: (1.5, "PostgreSQL — database exposed"),
    5900: (2.0, "VNC — remote desktop"),
    6379: (2.5, "Redis — no auth by default"),
    8080: (0.5, "HTTP alt — potentially unencrypted"),
    11211: (2.0, "Memcached — no auth by default"),
    27017: (2.5, "MongoDB — no auth by default"),
}

MAX_RISK = 10.0


def score_hosts(hosts: list[dict[str, Any]]) -> None:
    """Assign risk_score and risk_details to each host."""
    for host in hosts:
        score, details = _score_single(host)
        host["risk_score"] = score
        host["risk_details"] = json.dumps(details) if details else None


def _score_single(host: dict[str, Any]) -> tuple[float, list[str]]:
    open_ports = {p["port"] for p in host.get("ports", [])}
    details: list[str] = []
    score = 0.0

    for port in open_ports:
        if port in RISKY_PORTS:
            risk_val, desc = RISKY_PORTS[port]
            score += risk_val
            details.append(f"Port {port}: {desc} (+{risk_val})")

    # Bonus risk for many open ports
    if len(open_ports) > 20:
        bonus = 1.0
        score += bonus
        details.append(f"Large attack surface: {len(open_ports)} open ports (+{bonus})")

    # Cap at MAX_RISK
    score = min(score, MAX_RISK)

    return round(score, 1), details
