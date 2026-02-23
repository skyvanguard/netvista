interface Props {
  layout: string;
  onLayoutChange: (layout: string) => void;
  onFitView: () => void;
}

const LAYOUTS = [
  { value: 'cose-bilkent', label: 'Force-Directed' },
  { value: 'concentric', label: 'Concentric' },
  { value: 'circle', label: 'Circle' },
  { value: 'grid', label: 'Grid' },
];

export function GraphControls({ layout, onLayoutChange, onFitView }: Props) {
  return (
    <div className="flex items-center gap-2 flex-wrap">
      <span className="text-xs text-gray-500">Layout:</span>
      {LAYOUTS.map((l) => (
        <button
          key={l.value}
          onClick={() => onLayoutChange(l.value)}
          className={`text-xs px-2 py-1 rounded transition-colors ${
            layout === l.value
              ? 'bg-cyan-600 text-white'
              : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
          }`}
        >
          {l.label}
        </button>
      ))}
      <div className="w-px h-4 bg-gray-700 mx-1" />
      <button
        onClick={onFitView}
        className="text-xs px-2 py-1 rounded bg-gray-800 text-gray-400 hover:bg-gray-700 transition-colors"
      >
        Fit View
      </button>
    </div>
  );
}
