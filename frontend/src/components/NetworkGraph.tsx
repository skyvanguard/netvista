import { useEffect, useRef, useCallback } from 'react';
import cytoscape from 'cytoscape';
import coseBilkent from 'cytoscape-cose-bilkent';
import type { TopologyElements } from '../types';
import { cytoscapeStyles } from '../utils/cytoscape-styles';
import { layouts } from '../utils/layout-configs';

cytoscape.use(coseBilkent);

interface Props {
  elements: TopologyElements | null;
  layout: string;
  onNodeSelect: (nodeData: Record<string, unknown> | null) => void;
  onCyInit?: (cy: cytoscape.Core | null) => void;
}

export function NetworkGraph({ elements, layout, onNodeSelect, onCyInit }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);

  const initCy = useCallback(() => {
    if (!containerRef.current || !elements) return;

    if (cyRef.current) {
      cyRef.current.destroy();
    }

    const cy = cytoscape({
      container: containerRef.current,
      elements: [...elements.nodes, ...elements.edges],
      style: cytoscapeStyles,
      layout: (layouts[layout] || layouts['cose-bilkent']) as cytoscape.LayoutOptions,
      minZoom: 0.1,
      maxZoom: 5,
      wheelSensitivity: 0.3,
    });

    cy.on('tap', 'node[type!="subnet"]', (evt) => {
      onNodeSelect(evt.target.data());
    });

    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        onNodeSelect(null);
      }
    });

    cyRef.current = cy;
    onCyInit?.(cy);
  }, [elements, layout, onNodeSelect, onCyInit]);

  useEffect(() => {
    initCy();
    return () => {
      cyRef.current?.destroy();
      cyRef.current = null;
      onCyInit?.(null);
    };
  }, [initCy, onCyInit]);

  return (
    <div
      ref={containerRef}
      className="w-full h-full bg-gray-950 rounded-lg"
      style={{ minHeight: 500 }}
    />
  );
}
