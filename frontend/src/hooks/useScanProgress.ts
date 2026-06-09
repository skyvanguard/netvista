import { useEffect, useState } from 'react';
import { connectScanWS } from '../api';
import type { ScanProgress } from '../types';

const TERMINAL_STATES = new Set(['completed', 'failed']);
const MAX_BACKOFF_MS = 10_000;

export function useScanProgress(scanId: number | null) {
  const [progress, setProgress] = useState<ScanProgress | null>(null);

  useEffect(() => {
    if (!scanId) {
      setProgress(null);
      return;
    }

    let ws: WebSocket | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;
    let attempt = 0;
    let torndown = false; // component unmounted or scanId changed
    let finished = false; // scan reached a terminal state

    const open = () => {
      ws = connectScanWS(
        scanId,
        (data) => {
          const p = data as ScanProgress;
          setProgress(p);
          attempt = 0; // a healthy message resets the backoff
          if (TERMINAL_STATES.has(p.status)) {
            finished = true;
            ws?.close();
          }
        },
        () => {
          // onclose: reconnect with exponential backoff unless we're done.
          if (torndown || finished) return;
          const delay = Math.min(1000 * 2 ** attempt, MAX_BACKOFF_MS);
          attempt += 1;
          retryTimer = setTimeout(open, delay);
        },
      );
    };

    open();

    return () => {
      torndown = true;
      if (retryTimer) clearTimeout(retryTimer);
      ws?.close();
    };
  }, [scanId]);

  return progress;
}
