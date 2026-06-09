import { api } from '../api';
import type { CyContainer } from '../utils/cy';

interface Props {
  scanId: number;
  graphContainerRef?: React.RefObject<HTMLDivElement | null>;
}

export function ExportButtons({ scanId, graphContainerRef }: Props) {
  const exportPng = () => {
    const container = graphContainerRef?.current;
    if (!container) return;
    const cy = (container as CyContainer).__cy;
    if (!cy) return;

    const png = cy.png({ output: 'blob', bg: '#0a0a0f', full: true, scale: 2 });
    const url = URL.createObjectURL(png);
    const a = document.createElement('a');
    a.href = url;
    a.download = `netvista-topology-${scanId}.png`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-gray-500">Export:</span>
      <a
        href={api.getExportUrl(scanId, 'json')}
        download
        className="text-xs px-2 py-1 rounded bg-gray-800 text-gray-400 hover:bg-gray-700 transition-colors"
      >
        JSON
      </a>
      <a
        href={api.getExportUrl(scanId, 'csv')}
        download
        className="text-xs px-2 py-1 rounded bg-gray-800 text-gray-400 hover:bg-gray-700 transition-colors"
      >
        CSV
      </a>
      <button
        onClick={exportPng}
        className="text-xs px-2 py-1 rounded bg-gray-800 text-gray-400 hover:bg-gray-700 transition-colors"
      >
        PNG
      </button>
    </div>
  );
}
