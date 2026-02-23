import type { Scan } from '../types';
import { formatDate, formatDuration } from '../utils/formatters';

interface Props {
  scans: Scan[];
  selectedId: number | null;
  onSelect: (scan: Scan) => void;
  onDelete: (id: number) => void;
}

const STATUS_STYLES: Record<string, string> = {
  pending: 'bg-yellow-500/20 text-yellow-400',
  running: 'bg-cyan-500/20 text-cyan-400',
  completed: 'bg-green-500/20 text-green-400',
  failed: 'bg-red-500/20 text-red-400',
};

export function ScanHistory({ scans, selectedId, onSelect, onDelete }: Props) {
  if (scans.length === 0) {
    return (
      <div className="text-center text-gray-500 py-8 text-sm">
        No scans yet. Launch one to get started.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-medium text-gray-400 mb-3">Scan History</h3>
      {scans.map((scan) => (
        <div
          key={scan.id}
          onClick={() => onSelect(scan)}
          className={`p-3 rounded-lg border cursor-pointer transition-colors ${
            selectedId === scan.id
              ? 'border-cyan-500 bg-cyan-500/5'
              : 'border-gray-800 bg-gray-900 hover:border-gray-700'
          }`}
        >
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm font-mono">{scan.target}</span>
            <span className={`text-xs px-2 py-0.5 rounded-full ${STATUS_STYLES[scan.status] || ''}`}>
              {scan.status}
            </span>
          </div>
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>{scan.profile} &middot; {scan.host_count} hosts</span>
            <span>{formatDuration(scan.started_at, scan.finished_at)}</span>
          </div>
          <div className="flex items-center justify-between mt-1">
            <span className="text-xs text-gray-600">{formatDate(scan.created_at)}</span>
            <button
              onClick={(e) => { e.stopPropagation(); onDelete(scan.id); }}
              className="text-xs text-gray-600 hover:text-red-400 transition-colors"
            >
              Delete
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
