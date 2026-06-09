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

## Configuration

Backend env vars (all optional):

| Var | Default | Description |
|-----|---------|-------------|
| `API_KEY` | _(empty)_ | When set, every `/api` route (except `/api/health`) requires it via the `X-API-Key` header or `api_key` query param. Empty = open API. |
| `MAX_TARGET_ADDRESSES` | `65536` | Rejects scan targets whose range exceeds this many addresses (default = a /16). |
| `MAX_CONCURRENT_SCANS` | `2` | Max nmap scans running at once; extras stay `pending`. |

If `API_KEY` is set, the frontend must be built with a matching `VITE_API_KEY` (see `frontend/.env.example`).

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  React 18   │────▶│  FastAPI      │────▶│   nmap      │
│  Cytoscape  │◀────│  WebSocket    │◀────│   subprocess│
│  TailwindCSS│     │  aiosqlite    │     └─────────────┘
└─────────────┘     └──────────────┘
   :5175                :8040
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

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8040
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/scans | Launch a new scan |
| GET | /api/scans | List all scans |
| GET | /api/scans/{id} | Scan details |
| WS | /api/scans/{id}/ws | Real-time progress |
| GET | /api/scans/{id}/topology | Cytoscape elements |
| GET | /api/scans/{id}/hosts | All hosts |
| GET | /api/scans/{id}/hosts/{ip} | Host detail |
| GET | /api/scans/{id}/subnets | Subnet grouping |
| GET | /api/scans/{id}/export | Export JSON/CSV |
| DELETE | /api/scans/{id} | Delete scan |

## Requirements

- nmap installed (included in Docker image)
- Root/sudo for SYN scan and OS detection
- Python 3.12+, Node 20+

## License

MIT
