import { useState } from 'react';
import { api } from '../api';
import type { Scan, ScanProfile } from '../types';

const PROFILES: { value: ScanProfile; label: string; desc: string }[] = [
  { value: 'quick', label: 'Quick', desc: 'Ping sweep only (~30s for /24)' },
  { value: 'standard', label: 'Standard', desc: 'SYN scan, top 1000 ports, OS, traceroute (~15min)' },
  { value: 'deep', label: 'Deep', desc: 'Full port scan + scripts (~45min)' },
];

interface Props {
  onScanCreated: (scan: Scan) => void;
}

export function ScanLauncher({ onScanCreated }: Props) {
  const [target, setTarget] = useState('');
  const [profile, setProfile] = useState<ScanProfile>('standard');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!target.trim()) return;
    setLoading(true);
    setError('');
    try {
      const scan = await api.createScan(target.trim(), profile);
      onScanCreated(scan);
      setTarget('');
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-gray-900 rounded-lg p-6 border border-gray-800">
      <h2 className="text-lg font-semibold mb-4">New Scan</h2>

      <div className="mb-4">
        <label className="block text-sm text-gray-400 mb-1">Target</label>
        <input
          type="text"
          value={target}
          onChange={(e) => setTarget(e.target.value)}
          placeholder="192.168.1.0/24"
          className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm focus:outline-none focus:border-cyan-500"
        />
      </div>

      <div className="mb-4">
        <label className="block text-sm text-gray-400 mb-2">Profile</label>
        <div className="space-y-2">
          {PROFILES.map((p) => (
            <label
              key={p.value}
              className={`flex items-start gap-3 p-3 rounded cursor-pointer border transition-colors ${
                profile === p.value
                  ? 'border-cyan-500 bg-cyan-500/10'
                  : 'border-gray-700 hover:border-gray-600'
              }`}
            >
              <input
                type="radio"
                name="profile"
                value={p.value}
                checked={profile === p.value}
                onChange={() => setProfile(p.value)}
                className="mt-0.5"
              />
              <div>
                <div className="text-sm font-medium">{p.label}</div>
                <div className="text-xs text-gray-500">{p.desc}</div>
              </div>
            </label>
          ))}
        </div>
      </div>

      {error && <p className="text-red-400 text-sm mb-3">{error}</p>}

      <button
        type="submit"
        disabled={loading || !target.trim()}
        className="w-full bg-cyan-600 hover:bg-cyan-500 disabled:bg-gray-700 disabled:text-gray-500 text-white font-medium py-2 px-4 rounded transition-colors"
      >
        {loading ? 'Launching...' : 'Launch Scan'}
      </button>
    </form>
  );
}
