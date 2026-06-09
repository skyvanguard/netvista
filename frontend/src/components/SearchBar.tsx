import { useState, useEffect } from 'react';

interface Props {
  onSearch: (query: string) => void;
}

export function SearchBar({ onSearch }: Props) {
  const [query, setQuery] = useState('');

  // Debounce: only fire onSearch (which restyles every Cytoscape node) once
  // the user pauses typing, instead of on every keystroke.
  useEffect(() => {
    const id = setTimeout(() => onSearch(query), 200);
    return () => clearTimeout(id);
  }, [query, onSearch]);

  return (
    <input
      type="text"
      value={query}
      onChange={(e) => setQuery(e.target.value)}
      placeholder="Search by IP, hostname, port..."
      className="bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-sm w-64 focus:outline-none focus:border-cyan-500 placeholder-gray-600"
    />
  );
}
