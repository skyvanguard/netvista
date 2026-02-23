import { Routes, Route } from 'react-router-dom';
import { ScanPage } from './pages/ScanPage';
import { TopologyPage } from './pages/TopologyPage';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<ScanPage />} />
      <Route path="/topology/:scanId" element={<TopologyPage />} />
    </Routes>
  );
}
