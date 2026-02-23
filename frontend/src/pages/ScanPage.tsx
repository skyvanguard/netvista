import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';
import type { Scan } from '../types';
import { ScanLauncher } from '../components/ScanLauncher';
import { ScanProgress } from '../components/ScanProgress';
import { ScanHistory } from '../components/ScanHistory';
import { useScanProgress } from '../hooks/useScanProgress';

export function ScanPage() {
  const [scans, setScans] = useState<Scan[]>([]);
  const [activeScanId, setActiveScanId] = useState<number | null>(null);
  const progress = useScanProgress(activeScanId);
  const navigate = useNavigate();

  useEffect(() => {
    api.listScans().then(setScans).catch(console.error);
  }, []);

  // Poll active scan status
  useEffect(() => {
    if (!activeScanId) return;
    const interval = setInterval(async () => {
      try {
        const scan = await api.getScan(activeScanId);
        setScans((prev) => prev.map((s) => (s.id === scan.id ? scan : s)));
        if (scan.status === 'completed' || scan.status === 'failed') {
          clearInterval(interval);
        }
      } catch { /* ignore */ }
    }, 3000);
    return () => clearInterval(interval);
  }, [activeScanId]);

  const handleScanCreated = (scan: Scan) => {
    setScans((prev) => [scan, ...prev]);
    setActiveScanId(scan.id);
  };

  const handleSelect = (scan: Scan) => {
    if (scan.status === 'completed') {
      navigate(`/topology/${scan.id}`);
    } else if (scan.status === 'running') {
      setActiveScanId(scan.id);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await api.deleteScan(id);
      setScans((prev) => prev.filter((s) => s.id !== id));
      if (activeScanId === id) setActiveScanId(null);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-6">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold mb-2">NetVista</h1>
        <p className="text-gray-500">Network Topology Auto-Mapper</p>
      </div>

      <ScanLauncher onScanCreated={handleScanCreated} />

      {activeScanId && <ScanProgress progress={progress} />}

      {/* Show button to view topology when scan completes */}
      {progress?.status === 'completed' && activeScanId && (
        <button
          onClick={() => navigate(`/topology/${activeScanId}`)}
          className="w-full bg-green-600 hover:bg-green-500 text-white font-medium py-2 px-4 rounded transition-colors"
        >
          View Topology Map
        </button>
      )}

      <ScanHistory
        scans={scans}
        selectedId={activeScanId}
        onSelect={handleSelect}
        onDelete={handleDelete}
      />
    </div>
  );
}
