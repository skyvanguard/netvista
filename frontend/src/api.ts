import type { Scan, Host, Subnet, TopologyElements, ScanProfile } from './types';

const BASE = '/api';

// Optional API key, injected at build time. When set, the backend requires it
// on every /api call; sent as a header for JSON requests and as a query param
// for download links and the WebSocket (which can't set custom headers).
const API_KEY = import.meta.env.VITE_API_KEY ?? '';

function withKeyParam(url: string): string {
  if (!API_KEY) return url;
  const sep = url.includes('?') ? '&' : '?';
  return `${url}${sep}api_key=${encodeURIComponent(API_KEY)}`;
}

async function fetchJSON<T>(url: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (API_KEY) headers.set('X-API-Key', API_KEY);
  const res = await fetch(`${BASE}${url}`, { ...init, headers });
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
    withKeyParam(`${BASE}/scans/${scanId}/export?format=${format}`),
};

export function connectScanWS(
  scanId: number,
  onMessage: (data: unknown) => void,
  onClose?: () => void,
): WebSocket {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const url = withKeyParam(`${proto}//${window.location.host}${BASE}/scans/${scanId}/ws`);
  const ws = new WebSocket(url);
  ws.onmessage = (e) => onMessage(JSON.parse(e.data));
  ws.onclose = () => onClose?.();
  return ws;
}
