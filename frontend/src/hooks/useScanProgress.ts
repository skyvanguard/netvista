import { useEffect, useState, useRef } from 'react';
import { connectScanWS } from '../api';
import type { ScanProgress } from '../types';

export function useScanProgress(scanId: number | null) {
  const [progress, setProgress] = useState<ScanProgress | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!scanId) return;

    const ws = connectScanWS(
      scanId,
      (data) => setProgress(data as ScanProgress),
      () => setProgress((prev) => prev),
    );
    wsRef.current = ws;

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [scanId]);

  return progress;
}
