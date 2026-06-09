# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# NetVista — Network Topology Auto-Mapper

Scan networks with nmap, infer architecture, and render an interactive topology map.

## Stack
- Backend: Python 3.12 + FastAPI + aiosqlite
- Frontend: React 18 + TypeScript + Vite + TailwindCSS + Cytoscape.js (cose-bilkent layout)
- Docker: docker-compose; backend uses `network_mode: host` + `NET_RAW`/`NET_ADMIN` (nmap needs raw sockets)

## Commands
- Backend dev: `cd backend && pip install -r requirements.txt && uvicorn main:app --reload --port 8040`
- Frontend dev: `cd frontend && npm install && npm run dev` (serves on 5175)
- Frontend build / typecheck: `cd frontend && npm run build` (runs `tsc -b` then `vite build`)
- Full stack: `docker compose up --build` → frontend http://localhost:5175, API http://localhost:8040, docs `/docs`
- Backend tests: `cd backend && pip install -r requirements-dev.txt && pytest` (run a single file with `pytest tests/test_parser.py`)
- Backend lint: `cd backend && ruff check .` (config in `backend/ruff.toml`)

The backend has `pytest` unit tests for the pure logic and lifecycle (`tests/`: parser, categorizer, risk, subnet, target validation, orphan recovery, task cancellation, concurrency limit, host loader) and is linted with `ruff`. There is no frontend test runner yet.

## Ports & paths
- Backend: host 8040 → container 8000 conceptually, but in Docker the backend runs `--port 8040` under `network_mode: host`, so it binds 8040 directly on the host (no port mapping in compose).
- Frontend: host 5175 → container 80 (nginx).
- API base path is always `/api`. In dev, Vite proxies `/api` (including WebSocket) to `localhost:8040`; in Docker, nginx proxies `/api` to `host.docker.internal:8040`.
- SQLite DB: `DATABASE_URL` env (`/data/netvista.db` in Docker volume; `netvista.db` locally). WAL mode, `foreign_keys=ON`.

## Code Style
- Python: `from __future__ import annotations`, full type hints, async/await, Pydantic models for I/O.
- TypeScript: strict mode, ES modules, functional components.
- Conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`.

## Architecture

### Scan lifecycle (the core flow)
1. `POST /api/scans` (routers/scans.py) inserts a `pending` scan row, then fires `execute_scan` via `asyncio.create_task`, registers the task in `services/scan_registry.py`, and returns immediately.
2. `services/scan_manager.py::execute_scan` first waits on a `Semaphore(MAX_CONCURRENT_SCANS)` (env-configurable, default 2) — queued scans stay `pending` — then `_execute_scan` is the orchestrator: sets status `running` → runs nmap → categorizes → scores → persists hosts/ports/traceroute → builds & persists topology edges → sets `completed` (or `failed` with error). It broadcasts every state change over WebSocket.
3. State machine: `pending → running → completed | failed`.
4. `DELETE /api/scans/{id}` calls `scan_registry.cancel`, which cancels the running task; `nmap_runner` kills the nmap subprocess in a `finally` so it isn't orphaned.
5. On startup the `lifespan` hook runs `fail_orphaned_scans` — background tasks don't survive a restart, so any scan left `pending`/`running` is marked `failed`.

### Backend module responsibilities
- `scanner/profiles.py` — three profiles (`quick`/`standard`/`deep`) mapping to nmap flag lists. `standard`/`deep` need root for `-sS`/`-O`/`--traceroute`.
- `scanner/nmap_runner.py` — runs nmap to a temp `-oX` XML file, streams stdout to parse `"NN% done"` progress lines (mapped to the 0.0–0.9 range; parsing/finish fills 0.9–1.0).
- `scanner/parser.py` — `parse_nmap_xml` → list of host dicts. Only `state=up` hosts and `state=open` ports are kept. Produces nested `ports` and `traceroute` lists per host.
- `topology/categorizer.py` — `categorize_hosts` mutates each host adding `node_type`. **Precedence matters**: vendor match (camera/printer/network) wins first, then port+OS heuristics, then OS-only fallback. Edit the port/vendor sets at the top of the file to tune.
- `topology/risk.py` — `score_hosts` adds `risk_score` (additive per `RISKY_PORTS`, +1 for >20 open ports, capped at `MAX_RISK=10.0`) and a JSON `risk_details` string.
- `topology/subnet.py` — `group_by_subnet` **mutates hosts** by setting `host["subnet"]` (a `/24` key) and returns the grouping; `detect_gateways` picks the most common penultimate traceroute hop per subnet.
- `topology/builder.py` — `build_topology` produces edges (traceroute chains + `same_subnet` host→gateway edges); `to_cytoscape_elements` builds Cytoscape nodes/edges and **depends on `host["subnet"]` already being set** by `group_by_subnet` (it reads `host['subnet']` for the compound `parent`).

### Important: topology is computed twice
- Edges are computed **at scan time** and stored in `topology_edges`.
- But subnets and gateways are **recomputed on every read** in `routers/topology.py` (it reloads hosts, calls `group_by_subnet`+`detect_gateways`, then `to_cytoscape_elements`). The mutation side effect of `group_by_subnet` is what makes the Cytoscape conversion work — call it before `to_cytoscape_elements`.

### Database access pattern
- No connection pool. Every handler calls `get_db()` (a fresh `aiosqlite` connection) and closes it in `finally`. Follow this pattern in new routers.
- Schema lives as one `SCHEMA` string in `database.py`, applied on startup via the FastAPI `lifespan` hook. Cascading deletes rely on `foreign_keys=ON`, so deleting a scan removes its hosts/ports/hops/edges.

### WebSocket
- `services/ws_manager.py` holds an in-memory `dict[scan_id, list[WebSocket]]` (singleton `ws_manager`). Not shared across processes — assumes a single uvicorn worker.
- Client endpoint: `/api/scans/{id}/ws`. The frontend `useScanProgress` hook connects on scan launch; there is no reconnect/backfill logic, so progress before connect is lost.

### Frontend
- Two routes (`App.tsx`): `/` = `ScanPage` (launch + history), `/topology/:scanId` = `TopologyPage`.
- `src/api.ts` is the single fetch layer; all calls go through `/api`.
- `NetworkGraph.tsx` wraps Cytoscape. Subnet nodes are compound parents; host nodes set `parent: subnet-<cidr>`. The `cy` instance is stashed on `container.__cy` so `ExportButtons` can grab it for PNG export.
- Styling/layout config live in `src/utils/cytoscape-styles.ts` and `src/utils/layout-configs.ts`.

## Adding things
- New device category: add port/vendor sets + a branch in `categorizer.py::_categorize_single`, then a matching node style in `cytoscape-styles.ts`.
- New risky port: add to `RISKY_PORTS` in `risk.py`.
- New scan profile: add to `SCAN_PROFILES` in `profiles.py` and the `ScanCreate.profile` regex in `models.py`.
