import { useEffect, useState } from 'react';
import { api } from '../api';
import type { TopologyElements, Host } from '../types';

export function useTopology(scanId: number | null) {
  const [topology, setTopology] = useState<TopologyElements | null>(null);
  const [hosts, setHosts] = useState<Host[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!scanId) return;

    let cancelled = false;
    setLoading(true);
    setError(null);

    Promise.all([api.getTopology(scanId), api.getHosts(scanId)])
      .then(([topo, hostList]) => {
        if (cancelled) return;
        setTopology(topo);
        setHosts(hostList);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [scanId]);

  return { topology, hosts, loading, error };
}
