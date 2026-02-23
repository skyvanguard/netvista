import type { NodeType } from '../types';

export const NODE_TYPE_LABELS: Record<NodeType, string> = {
  server: 'Server',
  workstation: 'Workstation',
  network_device: 'Network Device',
  printer: 'Printer',
  camera: 'Camera',
  iot: 'IoT Device',
  unknown: 'Unknown',
};

export const NODE_TYPE_COLORS: Record<string, string> = {
  server: '#3b82f6',
  workstation: '#8b5cf6',
  network_device: '#f59e0b',
  printer: '#6b7280',
  camera: '#ef4444',
  iot: '#10b981',
  unknown: '#9ca3af',
};

export function riskColor(score: number): string {
  if (score >= 7) return '#ef4444';
  if (score >= 4) return '#f59e0b';
  if (score >= 1) return '#eab308';
  return '#22c55e';
}

export function riskLabel(score: number): string {
  if (score >= 7) return 'Critical';
  if (score >= 4) return 'High';
  if (score >= 1) return 'Medium';
  return 'Low';
}

export function formatDate(iso: string | null): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleString();
}

export function formatDuration(start: string | null, end: string | null): string {
  if (!start || !end) return '—';
  const ms = new Date(end).getTime() - new Date(start).getTime();
  const secs = Math.floor(ms / 1000);
  if (secs < 60) return `${secs}s`;
  const mins = Math.floor(secs / 60);
  const remSecs = secs % 60;
  return `${mins}m ${remSecs}s`;
}
