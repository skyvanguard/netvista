import type { Scan, Host, Subnet, TopologyElements, ScanProfile } from './types';

const BASE = '/api';

async function fetchJSON<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, init);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  if (res.status === 204) return undefined as unknown as T;
  return res.json();
}

export const api = {
  createScan: (target: string, profile: ScanProfile) =>
    fetchJSON<Scan>('/scans', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target, profile }),
    }),

  listScans: () => fetchJSON<Scan[]>('/scans'),
  getScan: (id: number) => fetchJSON<Scan>(`/scans/${id}`),
  deleteScan: (id: number) => fetchJSON<void>(`/scans/${id}`, { method: 'DELETE' }),

  getTopology: (scanId: number) => fetchJSON<TopologyElements>(`/scans/${scanId}/topology`),
  getHosts: (scanId: number) => fetchJSON<Host[]>(`/scans/${scanId}/hosts`),
  getHost: (scanId: number, ip: string) => fetchJSON<Host>(`/scans/${scanId}/hosts/${ip}`),
  getSubnets: (scanId: number) => fetchJSON<Subnet[]>(`/scans/${scanId}/subnets`),

  getExportUrl: (scanId: number, format: 'json' | 'csv') =>
    `${BASE}/scans/${scanId}/export?format=${format}`,
};

export function connectScanWS(
  scanId: number,
  onMessage: (data: unknown) => void,
  onClose?: () => void,
): WebSocket {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const ws = new WebSocket(`${proto}//${window.location.host}${BASE}/scans/${scanId}/ws`);
  ws.onmessage = (e) => onMessage(JSON.parse(e.data));
  ws.onclose = () => onClose?.();
  return ws;
}
