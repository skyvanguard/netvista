# NetVista

**Network Topology Auto-Mapper** — Scan networks with nmap, infer architecture, and generate interactive topology maps.

Point it at any network range and get a visual diagram of the architecture automatically.

## Features

- **3 scan profiles**: Quick (ping sweep), Standard (top 1000 ports + OS), Deep (full port scan + scripts)
- **Automatic topology inference**: subnet grouping, gateway detection via traceroute, device categorization
- **Device fingerprinting**: servers, workstations, network devices, printers, cameras, IoT
- **Risk scoring**: identifies dangerous exposed ports (FTP, Telnet, SMB, RDP, Redis, MongoDB...)
- **Interactive Cytoscape.js visualization**: compound subnet nodes, color-coded device types, click-to-inspect
- **Real-time progress**: WebSocket updates during scans
- **Export**: JSON, CSV, PNG

## Quick Start

```bash
docker compose up --build
```

- Frontend: http://localhost:5175
- API: http://localhost:8040
- API docs: http://localhost:8040/docs

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  React 18   │────>│  FastAPI      │────>│   nmap      │
│  Cytoscape  │<────│  WebSocket    │<────│   subprocess│
│  TailwindCSS│     │  aiosqlite    │     └─────────────┘
└─────────────┘     │  networkx     │
   :5175            └──────────────┘
                       :8040
```

## Scan Profiles

| Profile | Flags | Est. Time (/24) |
|---------|-------|-----------------|
| quick | `-sn -PE -PP -PS21,22,80,443` | ~30s |
| standard | `-sS -sV --top-ports 1000 -O --traceroute -T4` | ~15min |
| deep | `-sS -sV -sC -O -p- --traceroute -T3` | ~45min |

## Topology Algorithm

1. **Subnet grouping** — Group hosts by /24
2. **Gateway detection** — Most common penultimate traceroute hop per subnet
3. **Node categorization** — OS + ports + vendor fingerprinting
4. **Risk scoring** — Dangerous ports weighted and summed (max 10.0)

## Development

### Prerequisites

- Python 3.12+
- Node 20+
- nmap installed (included in Docker image)
- Root/sudo for SYN scan and OS detection

### Environment Variables

Copy `.env.example` to `.env` and adjust as needed:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `netvista.db` | SQLite database path |
| `HOST` | `0.0.0.0` | Backend bind address |
| `PORT` | `8040` | Backend port |
| `NMAP_PATH` | `nmap` | Path to nmap binary |
| `DATA_DIR` | `/data` or `.` | Data directory for DB storage |
| `CORS_ORIGINS` | `http://localhost:5175` | Allowed CORS origins (comma-separated) |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8040
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend
cd backend
pip install -r requirements-dev.txt
pytest

# Frontend
cd frontend
npm test
```

### Linting

```bash
# Backend
ruff check backend/
mypy backend/

# Frontend
cd frontend
npm run lint
npm run typecheck
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/scans | Launch a new scan |
| GET | /api/scans | List all scans (supports `?skip=0&limit=50`) |
| GET | /api/scans/{id} | Scan details |
| WS | /api/scans/{id}/ws | Real-time progress |
| GET | /api/scans/{id}/topology | Cytoscape elements |
| GET | /api/scans/{id}/hosts | All hosts |
| GET | /api/scans/{id}/hosts/{ip} | Host detail |
| GET | /api/scans/{id}/subnets | Subnet grouping |
| GET | /api/scans/{id}/export | Export JSON/CSV |
| DELETE | /api/scans/{id} | Delete scan |
| GET | /api/health | Health check |

## Docker

### Build & Run

```bash
docker compose up --build
```

### Resource Limits

The docker-compose file includes resource limits to prevent scans from consuming all system resources. Adjust `mem_limit` and `cpus` as needed.

### Healthchecks

Both containers include health checks. The backend exposes `/api/health` and the frontend checks nginx availability. Use `docker compose ps` to verify health status.

## Project Structure

```
netvista/
├── backend/
│   ├── main.py              # FastAPI app, CORS, router mounting
│   ├── config.py            # Environment-based configuration
│   ├── database.py          # SQLite schema and connection
│   ├── models.py            # Pydantic models with input validation
│   ├── routers/             # API route handlers
│   │   ├── scans.py         # CRUD + scan launch
│   │   ├── hosts.py         # Host queries
│   │   ├── topology.py      # Cytoscape graph data
│   │   └── export.py        # JSON/CSV export
│   ├── scanner/             # nmap integration
│   │   ├── nmap_runner.py   # Subprocess execution
│   │   ├── parser.py        # XML result parsing
│   │   └── profiles.py      # Scan flag profiles
│   ├── services/            # Business logic
│   │   ├── scan_manager.py  # Scan orchestration
│   │   ├── host_loader.py   # Shared host data loading
│   │   └── ws_manager.py    # WebSocket connections
│   └── topology/            # Topology inference
│       ├── builder.py       # Main topology builder
│       ├── subnet.py        # Subnet grouping
│       ├── categorizer.py   # Device categorization
│       └── risk.py          # Risk scoring
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # Router setup
│   │   ├── api.ts           # API client
│   │   ├── types.ts         # TypeScript interfaces
│   │   ├── components/      # React components
│   │   ├── hooks/           # Custom hooks (useScanProgress, useTopology, useCytoscape)
│   │   ├── pages/           # Page components (ScanPage, TopologyPage)
│   │   └── utils/           # Formatters, Cytoscape styles, layouts
│   ├── nginx.conf           # Production reverse proxy
│   └── Dockerfile           # Multi-stage build
├── docs/
│   └── plans/               # Design documents
├── docker-compose.yml
├── .env.example
├── .dockerignore
├── .editorconfig
└── .github/
    └── workflows/
        └── ci.yml           # Lint + typecheck + tests
```

## Roadmap

See [`docs/plans/2026-03-15-netvista-improvements-design.md`](docs/plans/2026-03-15-netvista-improvements-design.md) for the full improvement plan organized in 5 phases:

1. **Security** — Input validation, CORS, Docker hardening
2. **Testing & Quality** — pytest, vitest, logging, linting, TypeScript strictness
3. **Performance** — N+1 queries, pagination, nmap timeouts, concurrency limits
4. **DevOps** — GitHub Actions CI, Docker healthchecks, config files
5. **UX & Polish** — Error boundaries, accessibility, Cytoscape refactor, nginx hardening

## License

MIT
