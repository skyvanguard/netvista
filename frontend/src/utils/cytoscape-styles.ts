import type cytoscape from 'cytoscape';

const NODE_COLORS: Record<string, string> = {
  server: '#3b82f6',       // blue-500
  workstation: '#8b5cf6',  // violet-500
  network_device: '#f59e0b', // amber-500
  printer: '#6b7280',      // gray-500
  camera: '#ef4444',       // red-500
  iot: '#10b981',          // emerald-500
  unknown: '#9ca3af',      // gray-400
  subnet: 'transparent',
};

// @types/cytoscape types some numeric style props (e.g. text-margin-y) as
// string, so the literal is cast to the correct exported type at the end.
export const cytoscapeStyles = [
  // Subnet compound nodes
  {
    selector: 'node[type="subnet"]',
    style: {
      'shape': 'roundrectangle',
      'background-color': '#1e293b',
      'background-opacity': 0.3,
      'border-width': 2,
      'border-style': 'dashed',
      'border-color': '#475569',
      'label': 'data(label)',
      'text-valign': 'top',
      'text-halign': 'center',
      'font-size': 14,
      'color': '#94a3b8',
      'padding': '30px' as unknown as number,
      'text-margin-y': -10,
    },
  },
  // Regular host nodes
  {
    selector: 'node[type!="subnet"]',
    style: {
      'width': 40,
      'height': 40,
      'label': 'data(label)',
      'text-valign': 'bottom',
      'text-halign': 'center',
      'font-size': 10,
      'color': '#e2e8f0',
      'text-margin-y': 6,
      'background-color': (ele: cytoscape.NodeSingular) =>
        NODE_COLORS[ele.data('type')] || NODE_COLORS.unknown,
      'border-width': 2,
      'border-color': '#1e293b',
      'text-max-width': '80px',
      'text-wrap': 'ellipsis',
    },
  },
  // Gateway nodes — diamond, larger
  {
    selector: 'node[?isGateway]',
    style: {
      'shape': 'diamond',
      'width': 55,
      'height': 55,
      'border-width': 3,
      'border-color': '#f59e0b',
    },
  },
  // High risk nodes
  {
    selector: 'node[riskScore >= 7]',
    style: {
      'border-width': 3,
      'border-color': '#ef4444',
    },
  },
  // Traceroute edges
  {
    selector: 'edge[type="traceroute"]',
    style: {
      'width': 2,
      'line-color': '#475569',
      'target-arrow-color': '#475569',
      'target-arrow-shape': 'triangle',
      'curve-style': 'bezier',
      'arrow-scale': 0.8,
    },
  },
  // Same-subnet edges
  {
    selector: 'edge[type="same_subnet"]',
    style: {
      'width': 1,
      'line-color': '#334155',
      'line-style': 'dashed',
      'curve-style': 'bezier',
    },
  },
  // Selected node
  {
    selector: 'node:selected',
    style: {
      'border-width': 4,
      'border-color': '#22d3ee',
      'overlay-opacity': 0.1,
      'overlay-color': '#22d3ee',
    },
  },
] as unknown as cytoscape.StylesheetStyle[];
