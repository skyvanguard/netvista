import { useRef, useCallback } from 'react';
import type cytoscape from 'cytoscape';

export function useCytoscapeRef() {
  const cyRef = useRef<cytoscape.Core | null>(null);

  const setCy = useCallback((cy: cytoscape.Core | null) => {
    cyRef.current = cy;
  }, []);

  return { cyRef, setCy };
}
