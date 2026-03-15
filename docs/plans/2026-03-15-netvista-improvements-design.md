# NetVista Improvements Design

**Date:** 2026-03-15
**Goal:** Portfolio project ready for production use
**Approach:** 5 phases organized by severity (critical first)

---

## Phase 1 — Security

### 1.1 Target Input Validation (Command Injection Fix)
- Add Pydantic validator in `models.py` using `ipaddress.ip_network()` and hostname regex
- Reject any input that is not a valid IP, CIDR, or hostname
- Blocks command injection at the root

### 1.2 Restrictive CORS
- Change `allow_origins` to env var `CORS_ORIGINS` with default `http://localhost:5175`
- Remove `allow_credentials=True` (no auth in use)

### 1.3 Docker Non-Root
- Create `appuser` in both Dockerfiles
- Backend: grant `NET_RAW` capability to nmap binary via `setcap` instead of running as root
- Frontend: nginx non-root config

### 1.4 Silent Exception Handling
- Replace bare `except Exception` with structured logging

---

## Phase 2 — Testing & Code Quality

### 2.1 Backend Tests (pytest + pytest-asyncio)
- `requirements-dev.txt` with pytest, pytest-asyncio, httpx
- Tests for: model validation, CRUD endpoints, scanner parser, topology builder, risk scoring
- In-memory DB fixtures

### 2.2 Frontend Tests (vitest + testing-library)
- Add vitest, @testing-library/react, @testing-library/jest-dom
- Tests for: hooks (useScanProgress, useTopology), utils (formatters), key components (ScanLauncher, HostDetailPanel)

### 2.3 Backend Logging
- Configure `logging` with structured format across all modules
- Levels: ERROR for exceptions, INFO for scans/events, DEBUG for queries
- `LOG_LEVEL` env var

### 2.4 Linting
- Backend: ruff + mypy in `requirements-dev.txt`
- Frontend: eslint with React/TypeScript config
- package.json scripts: `lint`, `typecheck`

### 2.5 TypeScript Strictness
- Enable `noUnusedLocals` and `noUnusedParameters`
- Remove all `as any` — create typed interfaces for Cytoscape
- Change `catch (err: any)` to `catch (err: unknown)` with type guards

### 2.6 Consistent Return Types
- Align `response_model` with actual return types in routers

---

## Phase 3 — Performance & Architecture

### 3.1 N+1 Query Fix
- Refactor `routers/hosts.py` to use JOINs: single query for hosts + ports + traceroute
- Create shared `_load_hosts_with_data()` in `services/host_loader.py`
- Remove duplication between hosts, topology, and export routers

### 3.2 Pagination
- Add `skip` and `limit` query params to `list_scans` (default limit=50)
- Response with metadata: `{items: [...], total: N, skip: 0, limit: 50}`

### 3.3 Nmap Timeout & Concurrency
- Configurable timeout per scan profile (quick=60s, standard=300s, deep=600s)
- `asyncio.Semaphore(3)` to limit concurrent scans
- Return 429 Too Many Requests when limit exceeded

### 3.4 WebSocket Broadcast
- Replace sequential loop with `asyncio.gather(*sends, return_exceptions=True)`

### 3.5 Frontend Search Debounce
- 300ms debounce on SearchBar before filtering nodes

### 3.6 Frontend Memoization
- `useMemo` for riskDetails parsing in HostDetailPanel
- `useCallback` for handlers in TopologyPage
- Avoid recreating Cytoscape on layout change — use `cy.layout().run()`

### 3.7 Pure Functions
- `group_by_subnet` must not mutate objects — create copies with spread operator

### 3.8 DB Connection Management
- Use FastAPI dependency injection with `Depends(get_db)` and proper context manager

---

## Phase 4 — DevOps

### 4.1 CI/CD with GitHub Actions
- `.github/workflows/ci.yml`: lint + typecheck + tests on every push/PR
- Matrix: Python 3.12, Node 20
- Backend: ruff check, mypy, pytest
- Frontend: eslint, tsc --noEmit, vitest

### 4.2 Docker Healthchecks
- Backend: `HEALTHCHECK CMD curl -f http://localhost:8040/api/health || exit 1`
- Add `/api/health` endpoint
- Frontend: `HEALTHCHECK CMD curl -f http://localhost:80 || exit 1`
- `depends_on` with `service_healthy` condition in docker-compose

### 4.3 Missing Config Files
- `.dockerignore` — exclude `.git`, `node_modules`, `__pycache__`, `*.db`
- `.env.example` — document all env vars
- `.editorconfig` — editor consistency

### 4.4 Docker Resource Limits
- Add `mem_limit` and `cpus` in docker-compose

---

## Phase 5 — UX & Polish

### 5.1 Error Boundaries (Frontend)
- Add `ErrorBoundary` component for render error capture
- User-friendly UI instead of white screen
- Add error states for all API calls (loading, error, success)

### 5.2 Cytoscape Refactor
- Extract Cytoscape logic to `useCytoscape` custom hook
- Use React ref instead of storing instance on DOM element (`__cy`)
- Create `CytoscapeContext` to share instance between components

### 5.3 Accessibility
- ARIA labels on inputs (ScanLauncher, SearchBar)
- `role="status"` and `aria-live="polite"` on loading indicators
- Semantic HTML: `<section>`, `<nav>`, `<main>` where appropriate
- Visible focus indicators on buttons

### 5.4 Nginx Hardening
- gzip compression
- Content-Security-Policy header
- X-Frame-Options, X-Content-Type-Options headers
- Cache headers for static assets

### 5.5 Updated README
- New structure, testing instructions, env vars, contribution guide
