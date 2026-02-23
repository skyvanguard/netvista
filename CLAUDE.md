# NetVista — Network Topology Auto-Mapper

## Stack
- Backend: Python 3.12 + FastAPI + aiosqlite + networkx
- Frontend: React 18 + TypeScript + Vite + TailwindCSS + Cytoscape.js
- Docker: docker-compose with network_mode: host (nmap needs raw sockets)

## Commands
- Backend dev: `cd backend && pip install -r requirements.txt && uvicorn main:app --reload --port 8040`
- Frontend dev: `cd frontend && npm install && npm run dev`
- Docker: `docker compose up --build`

## Code Style
- Python: type hints, async/await, Pydantic models
- TypeScript: strict mode, ES modules, functional components
- Conventional commits: feat:, fix:, refactor:, docs:

## Architecture
- Backend ports: 8040 (host) → 8000 (container)
- Frontend ports: 5175 (host) → 80 (container)
- SQLite DB stored in /data/netvista.db (Docker volume)
- WebSocket at /api/scans/{id}/ws for real-time scan progress
- Topology algorithm: subnet grouping → gateway detection → categorization → risk scoring
