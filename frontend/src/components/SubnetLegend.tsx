import { NODE_TYPE_LABELS, NODE_TYPE_COLORS } from '../utils/formatters';

const TYPES = Object.keys(NODE_TYPE_LABELS) as Array<keyof typeof NODE_TYPE_LABELS>;

export function SubnetLegend() {
  return (
    <div className="flex flex-wrap gap-3">
      {TYPES.map((type) => (
        <div key={type} className="flex items-center gap-1.5">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: NODE_TYPE_COLORS[type] }}
          />
          <span className="text-xs text-gray-400">{NODE_TYPE_LABELS[type]}</span>
        </div>
      ))}
      <div className="flex items-center gap-1.5">
        <div className="w-3 h-3 rotate-45 bg-amber-500" />
        <span className="text-xs text-gray-400">Gateway</span>
      </div>
      <div className="flex items-center gap-1.5">
        <div className="w-3 h-3 rounded-full border-2 border-red-500" />
        <span className="text-xs text-gray-400">High Risk</span>
      </div>
    </div>
  );
}
