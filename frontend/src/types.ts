export interface Scan {
  id: number;
  target: string;
  profile: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  started_at: string | null;
  finished_at: string | null;
  host_count: number;
  error: string | null;
  created_at: string;
}

export interface Port {
  port: number;
  protocol: string;
  state: string;
  service: string | null;
  version: string | null;
}

export interface TracerouteHop {
  hop: number;
  ip: string | null;
  rtt: number | null;
  hostname: string | null;
}

export interface Host {
  id: number;
  ip: string;
  hostname: string | null;
  mac: string | null;
  vendor: string | null;
  os_name: string | null;
  os_accuracy: number | null;
  state: string;
  node_type: string;
  risk_score: number;
  risk_details: string | null;
  ports: Port[];
  traceroute: TracerouteHop[];
}

export interface Subnet {
  subnet: string;
  gateway: string | null;
  host_count: number;
  hosts: string[];
}

export interface TopologyElements {
  nodes: { data: Record<string, unknown> }[];
  edges: { data: Record<string, unknown> }[];
}

export interface ScanProgress {
  scan_id: number;
  status: string;
  progress: number;
  message: string;
  // null while the scan is running (count is only known once it finishes).
  hosts_found: number | null;
}

export type NodeType = 'server' | 'workstation' | 'network_device' | 'printer' | 'camera' | 'iot' | 'unknown';
export type ScanProfile = 'quick' | 'standard' | 'deep';
