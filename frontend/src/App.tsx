import { Routes, Route } from 'react-router-dom';
import { Suspense, lazy } from 'react';
import { ScanPage } from './pages/ScanPage';

// Lazy-load the topology view so Cytoscape (the bulk of the bundle) is only
// fetched when the user actually opens a topology map.
const TopologyPage = lazy(() =>
  import('./pages/TopologyPage').then((m) => ({ default: m.TopologyPage })),
);

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<ScanPage />} />
      <Route
        path="/topology/:scanId"
        element={
          <Suspense
            fallback={
              <div className="h-screen flex items-center justify-center text-cyan-400 text-sm">
                Loading topology…
              </div>
            }
          >
            <TopologyPage />
          </Suspense>
        }
      />
    </Routes>
  );
}
