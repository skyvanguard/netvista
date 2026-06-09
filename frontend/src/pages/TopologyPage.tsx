import { useState, useCallback, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useTopology } from '../hooks/useTopology';
import { NetworkGraph } from '../components/NetworkGraph';
import { GraphControls } from '../components/GraphControls';
import { HostDetailPanel } from '../components/HostDetailPanel';
import { SubnetLegend } from '../components/SubnetLegend';
import { SearchBar } from '../components/SearchBar';
import { ExportButtons } from '../components/ExportButtons';
import type { Host } from '../types';

export function TopologyPage() {
  const { scanId } = useParams<{ scanId: string }>();
  const id = scanId ? parseInt(scanId, 10) : null;
  const { topology, hosts, loading, error } = useTopology(id);
  const [layout, setLayout] = useState('cose-bilkent');
  const [selectedHost, setSelectedHost] = useState<Host | null>(null);
  const graphContainerRef = useRef<HTMLDivElement>(null);

  const handleNodeSelect = useCallback(
    (nodeData: Record<string, unknown> | null) => {
      if (!nodeData) {
        setSelectedHost(null);
        return;
      }
      const ip = nodeData.ip as string;
      const host = hosts.find((h) => h.ip === ip) || null;
      setSelectedHost(host);
    },
    [hosts],
  );

  const handleSearch = useCallback(
    (query: string) => {
      const container = graphContainerRef.current;
      if (!container) return;
      const cy = (container as any).__cy;
      if (!cy) return;

      // Empty query: restore full opacity on every node.
      if (!query.trim()) {
        cy.nodes().style('opacity', 1);
        return;
      }

      const q = query.toLowerCase();
      cy.nodes().forEach((node: any) => {
        const data = node.data();
        const match =
          data.ip?.toLowerCase().includes(q) ||
          data.label?.toLowerCase().includes(q) ||
          String(data.portCount).includes(q);
        node.style('opacity', match || data.type === 'subnet' ? 1 : 0.15);
      });
    },
    [],
  );

  const handleFitView = () => {
    const container = graphContainerRef.current;
    if (!container) return;
    const cy = (container as any).__cy;
    cy?.fit(undefined, 50);
  };

  if (!id) return <div className="p-6">Invalid scan ID</div>;

  return (
    <div className="h-screen flex flex-col">
      {/* Top bar */}
      <div className="bg-gray-900 border-b border-gray-800 px-4 py-3">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-4">
            <Link to="/" className="text-cyan-400 hover:text-cyan-300 text-sm">&larr; Scans</Link>
            <h1 className="text-lg font-semibold">Topology — Scan #{id}</h1>
            <span className="text-xs text-gray-500">{hosts.length} hosts</span>
          </div>
          <div className="flex items-center gap-4">
            <SearchBar onSearch={handleSearch} />
            <ExportButtons scanId={id} graphContainerRef={graphContainerRef} />
          </div>
        </div>
        <div className="flex items-center justify-between mt-2 flex-wrap gap-3">
          <SubnetLegend />
          <GraphControls layout={layout} onLayoutChange={setLayout} onFitView={handleFitView} />
        </div>
      </div>

      {/* Main area */}
      <div className="flex-1 flex relative overflow-hidden">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-950/80 z-10">
            <div className="text-cyan-400 text-sm">Loading topology...</div>
          </div>
        )}

        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-950/80 z-10">
            <div className="text-red-400 text-sm">Error: {error}</div>
          </div>
        )}

        <div ref={graphContainerRef} className="flex-1">
          <NetworkGraph elements={topology} layout={layout} onNodeSelect={handleNodeSelect} />
        </div>

        {selectedHost && (
          <div className="absolute top-4 right-4 z-20">
            <HostDetailPanel host={selectedHost} onClose={() => setSelectedHost(null)} />
          </div>
        )}
      </div>
    </div>
  );
}
