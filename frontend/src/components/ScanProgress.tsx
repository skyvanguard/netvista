import type { ScanProgress as ScanProgressType } from '../types';

interface Props {
  progress: ScanProgressType | null;
}

export function ScanProgress({ progress }: Props) {
  if (!progress) return null;

  const pct = Math.round(progress.progress * 100);
  const isRunning = progress.status === 'running';
  const isFailed = progress.status === 'failed';

  return (
    <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium">
          {isRunning && 'Scanning...'}
          {progress.status === 'completed' && 'Scan Complete'}
          {isFailed && 'Scan Failed'}
        </span>
        <span className="text-sm text-gray-400">{pct}%</span>
      </div>

      <div className="w-full bg-gray-800 rounded-full h-2 mb-2">
        <div
          className={`h-2 rounded-full transition-all duration-300 ${
            isFailed ? 'bg-red-500' : progress.status === 'completed' ? 'bg-green-500' : 'bg-cyan-500'
          }`}
          style={{ width: `${pct}%` }}
        />
      </div>

      <p className="text-xs text-gray-500 truncate">{progress.message}</p>

      {progress.hosts_found > 0 && (
        <p className="text-xs text-gray-400 mt-1">
          {progress.hosts_found} hosts found
        </p>
      )}
    </div>
  );
}
