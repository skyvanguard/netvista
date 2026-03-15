from __future__ import annotations

import ipaddress
import re

from pydantic import BaseModel, Field, field_validator

_HOSTNAME_RE = re.compile(
    r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})*$"
)


class ScanCreate(BaseModel):
    target: str = Field(..., examples=["192.168.1.0/24"])
    profile: str = Field(default="standard", pattern="^(quick|standard|deep)$")

    @field_validator("target")
    @classmethod
    def validate_target(cls, v: str) -> str:
        v = v.strip()
        # Try parsing as a single IP address
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            pass
        # Try parsing as a CIDR network
        try:
            ipaddress.ip_network(v, strict=False)
            return v
        except ValueError:
            pass
        # Try matching as a hostname
        if len(v) <= 253 and _HOSTNAME_RE.match(v):
            return v
        raise ValueError(
            "target must be a valid IP address, CIDR network, or hostname"
        )


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


class ScanDetail(ScanOut):
    hosts: list[HostOut] = []


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
