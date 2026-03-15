import { useMemo } from 'react';
import type { Host } from '../types';
import { RiskBadge } from './RiskBadge';
import { NODE_TYPE_LABELS, NODE_TYPE_COLORS } from '../utils/formatters';

interface Props {
  host: Host | null;
  onClose: () => void;
}

export function HostDetailPanel({ host, onClose }: Props) {
  const riskDetails = useMemo(() => {
    if (!host?.risk_details) return [];
    try {
      return JSON.parse(host.risk_details) as string[];
    } catch {
      return [];
    }
  }, [host?.risk_details]);

  if (!host) return null;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 w-80 max-h-[calc(100vh-200px)] overflow-y-auto">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold font-mono">{host.ip}</h3>
        <button onClick={onClose} className="text-gray-500 hover:text-gray-300 text-lg leading-none">&times;</button>
      </div>

      {host.hostname && (
        <p className="text-xs text-gray-400 mb-2">{host.hostname}</p>
      )}

      <div className="flex items-center gap-2 mb-3">
        <span
          className="text-xs px-2 py-0.5 rounded-full"
          style={{
            backgroundColor: `${NODE_TYPE_COLORS[host.node_type] || NODE_TYPE_COLORS.unknown}20`,
            color: NODE_TYPE_COLORS[host.node_type] || NODE_TYPE_COLORS.unknown,
          }}
        >
          {NODE_TYPE_LABELS[host.node_type as keyof typeof NODE_TYPE_LABELS] || host.node_type}
        </span>
        <RiskBadge score={host.risk_score} />
      </div>

      {/* OS Info */}
      {host.os_name && (
        <div className="mb-3">
          <h4 className="text-xs text-gray-500 mb-1">OS Detection</h4>
          <p className="text-sm">{host.os_name}</p>
          {host.os_accuracy != null && (
            <p className="text-xs text-gray-500">Accuracy: {host.os_accuracy}%</p>
          )}
        </div>
      )}

      {/* Network Info */}
      {(host.mac || host.vendor) && (
        <div className="mb-3">
          <h4 className="text-xs text-gray-500 mb-1">Network</h4>
          {host.mac && <p className="text-xs font-mono text-gray-300">{host.mac}</p>}
          {host.vendor && <p className="text-xs text-gray-400">{host.vendor}</p>}
        </div>
      )}

      {/* Open Ports */}
      {host.ports.length > 0 && (
        <div className="mb-3">
          <h4 className="text-xs text-gray-500 mb-1">Open Ports ({host.ports.length})</h4>
          <div className="space-y-1 max-h-40 overflow-y-auto">
            {host.ports.map((p) => (
              <div key={`${p.port}/${p.protocol}`} className="flex items-center justify-between text-xs">
                <span className="font-mono text-cyan-400">{p.port}/{p.protocol}</span>
                <span className="text-gray-400 truncate ml-2">
                  {p.service}{p.version ? ` ${p.version}` : ''}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Risk Details */}
      {riskDetails.length > 0 && (
        <div>
          <h4 className="text-xs text-gray-500 mb-1">Risk Details</h4>
          <div className="space-y-1">
            {riskDetails.map((detail, i) => (
              <p key={i} className="text-xs text-red-400/80">{detail}</p>
            ))}
          </div>
        </div>
      )}

      {/* Traceroute */}
      {host.traceroute.length > 0 && (
        <div className="mt-3">
          <h4 className="text-xs text-gray-500 mb-1">Traceroute ({host.traceroute.length} hops)</h4>
          <div className="space-y-0.5">
            {host.traceroute.map((hop) => (
              <div key={hop.hop} className="flex items-center gap-2 text-xs">
                <span className="text-gray-600 w-4 text-right">{hop.hop}</span>
                <span className="font-mono text-gray-300">{hop.ip || '*'}</span>
                {hop.rtt != null && <span className="text-gray-500">{hop.rtt.toFixed(1)}ms</span>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
