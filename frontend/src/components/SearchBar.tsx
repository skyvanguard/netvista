import { useState, useEffect, useRef } from 'react';

interface Props {
  onSearch: (query: string) => void;
}

export function SearchBar({ onSearch }: Props) {
  const [query, setQuery] = useState('');
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => {
      onSearch(query);
    }, 300);
    return () => clearTimeout(timeoutRef.current);
  }, [query, onSearch]);

  return (
    <input
      type="text"
      value={query}
      onChange={(e) => setQuery(e.target.value)}
      placeholder="Search by IP, hostname, port..."
      aria-label="Search nodes"
      className="bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-sm w-64 focus:outline-none focus:border-cyan-500 placeholder-gray-600"
    />
  );
}
