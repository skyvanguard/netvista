from __future__ import annotations

from pydantic import BaseModel, Field


class ScanCreate(BaseModel):
    target: str = Field(..., examples=["192.168.1.0/24"])
    profile: str = Field(default="standard", pattern="^(quick|standard|deep)$")


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
