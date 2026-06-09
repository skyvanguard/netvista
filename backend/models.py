from __future__ import annotations

import ipaddress
import re

from pydantic import BaseModel, Field, field_validator

from config import MAX_TARGET_ADDRESSES

# Hostname per RFC 1123 (labels of letters/digits/hyphens, dot-separated).
_HOSTNAME_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*$"
)


class ScanCreate(BaseModel):
    target: str = Field(..., examples=["192.168.1.0/24"])
    profile: str = Field(default="standard", pattern="^(quick|standard|deep)$")

    @field_validator("target")
    @classmethod
    def validate_target(cls, value: str) -> str:
        """Accept only an IP, CIDR range, or hostname.

        Prevents nmap argument injection — without this a value like
        '--script=...' or '-oN /path' would be passed through as an nmap flag.
        """
        target = value.strip()
        if not target or target.startswith("-"):
            raise ValueError("target must be an IP address, CIDR range, or hostname")
        try:
            network = ipaddress.ip_network(target, strict=False)
        except ValueError:
            network = None
        if network is not None:
            if network.num_addresses > MAX_TARGET_ADDRESSES:
                raise ValueError(
                    f"target range too large: {network.num_addresses} addresses "
                    f"(max {MAX_TARGET_ADDRESSES})"
                )
            return target
        if _HOSTNAME_RE.match(target):
            return target
        raise ValueError("target must be an IP address, CIDR range, or hostname")


class PortOut(BaseModel):
    port: int
    protocol: str
    state: str
    service: str | None = None
    version: str | None = None


class TracerouteHopOut(BaseModel):
    hop: int
    ip: str | None = None
    rtt: float | None = None
    hostname: str | None = None


class HostOut(BaseModel):
    id: int
    ip: str
    hostname: str | None = None
    mac: str | None = None
    vendor: str | None = None
    os_name: str | None = None
    os_accuracy: int | None = None
    state: str
    node_type: str
    risk_score: float
    risk_details: str | None = None
    ports: list[PortOut] = []
    traceroute: list[TracerouteHopOut] = []


class ScanOut(BaseModel):
    id: int
    target: str
    profile: str
    status: str
    started_at: str | None = None
    finished_at: str | None = None
    host_count: int
    error: str | None = None
    created_at: str


class SubnetOut(BaseModel):
    subnet: str
    gateway: str | None = None
    host_count: int
    hosts: list[str]


class TopologyNode(BaseModel):
    data: dict


class TopologyEdge(BaseModel):
    data: dict


class TopologyOut(BaseModel):
    nodes: list[TopologyNode]
    edges: list[TopologyEdge]


class ScanProgress(BaseModel):
    scan_id: int
    status: str
    progress: float = 0.0
    message: str = ""
    hosts_found: int = 0
