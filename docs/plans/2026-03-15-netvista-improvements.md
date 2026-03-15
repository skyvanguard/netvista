# NetVista Improvements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform NetVista from an MVP into a production-ready, portfolio-quality network topology mapper with security hardening, full test coverage, performance optimizations, CI/CD, and polished UX.

**Architecture:** 5 phases organized by severity — security first, then testing/quality, performance, DevOps, and UX polish. Each phase produces a working commit. Backend is Python 3.12 + FastAPI + aiosqlite, frontend is React 18 + TypeScript + Vite + TailwindCSS + Cytoscape.js.

**Tech Stack:** Python (pytest, ruff, mypy), TypeScript (vitest, eslint), Docker, GitHub Actions, nginx

---

## Phase 1: Security

### Task 1: Add target input validation to block command injection

**Files:**
- Modify: `backend/models.py:1-8`
- Modify: `backend/scanner/nmap_runner.py:14-24`

**Step 1: Add Pydantic validator to ScanCreate model**

In `backend/models.py`, add `ipaddress` import and a `@field_validator` for `target`:

```python
from __future__ import annotations

import ipaddress
import re
from pydantic import BaseModel, Field, field_validator

# Valid hostname pattern (RFC 1123)
_HOSTNAME_RE = re.compile(
    r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})*$"
)


class ScanCreate(BaseModel):
    target: str = Field(..., examples=["192.168.1.0/24"])
    profile: str = Field(default="standard", pattern="^(quick|standard|deep)$")

    @field_validator("target")
    @classmethod
    def validate_target(cls, v: str) -> str:
        v = v.strip()
        # Try IP address
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            pass
        # Try CIDR network
        try:
            ipaddress.ip_network(v, strict=False)
            return v
        except ValueError:
            pass
        # Try hostname
        if _HOSTNAME_RE.match(v) and len(v) <= 253:
            return v
        raise ValueError(
            "target must be a valid IP address, CIDR range, or hostname"
        )
```

**Step 2: Run backend to verify validation works**

Run: `cd backend && python -c "from models import ScanCreate; ScanCreate(target='192.168.1.0/24'); print('CIDR OK'); ScanCreate(target='10.0.0.1'); print('IP OK'); ScanCreate(target='example.com'); print('Hostname OK')"`
Expected: All three print OK.

Run: `cd backend && python -c "from models import ScanCreate; ScanCreate(target='192.168.1.0/24; rm -rf /')" 2>&1 || echo "REJECTED"`
Expected: ValidationError — REJECTED

**Step 3: Commit**

```
fix: add target input validation to prevent command injection
```

---

### Task 2: Restrict CORS configuration

**Files:**
- Modify: `backend/config.py:1-8`
- Modify: `backend/main.py:23-29`

**Step 1: Add CORS_ORIGINS to config.py**

```python
import os
from pathlib import Path

DATABASE_URL: str = os.getenv("DATABASE_URL", "netvista.db")
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", "8040"))
NMAP_PATH: str = os.getenv("NMAP_PATH", "nmap")
DATA_DIR: Path = Path(os.getenv("DATA_DIR", "/data" if os.path.exists("/data") else "."))
CORS_ORIGINS: list[str] = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:5175").split(",")
    if o.strip()
]
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
```

**Step 2: Update main.py CORS middleware**

Replace lines 23-29 of `backend/main.py`:

```python
from config import CORS_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)
```

**Step 3: Commit**

```
fix: restrict CORS to configured origins
```

---

### Task 3: Add non-root user to Docker containers

**Files:**
- Modify: `backend/Dockerfile`
- Modify: `frontend/Dockerfile`

**Step 1: Update backend Dockerfile**

```dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    nmap libcap2-bin curl \
    && rm -rf /var/lib/apt/lists/* \
    && setcap cap_net_raw,cap_net_admin+eip /usr/bin/nmap

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /data && \
    groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app /data

USER appuser

EXPOSE 8040

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8040/api/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8040"]
```

**Step 2: Update frontend Dockerfile**

```dockerfile
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost:80 || exit 1
```

**Step 3: Commit**

```
fix: run Docker containers as non-root with healthchecks
```

---

### Task 4: Replace silent exception handling with logging

**Files:**
- Create: `backend/log.py`
- Modify: `backend/services/ws_manager.py:22-31`
- Modify: `backend/services/scan_manager.py:119-127`
- Modify: `backend/main.py` (add logging config to lifespan)

**Step 1: Create logging module**

Create `backend/log.py`:

```python
import logging
import sys

from config import LOG_LEVEL


def setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )
```

**Step 2: Initialize logging in main.py lifespan**

In `backend/main.py`, update the lifespan:

```python
from log import setup_logging

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    await init_db()
    yield
```

**Step 3: Add logging to ws_manager.py**

Replace the broadcast method in `backend/services/ws_manager.py`:

```python
import logging

logger = logging.getLogger(__name__)

# In broadcast method, replace bare except:
            except Exception:
                logger.warning("WebSocket send failed for scan %d, removing connection", scan_id)
                dead.append(ws)
```

**Step 4: Add logging to scan_manager.py**

Add at top of `backend/services/scan_manager.py`:

```python
import logging

logger = logging.getLogger(__name__)
```

Replace the outer except block (lines 119-125):

```python
    except Exception as exc:
        logger.exception("Unexpected error in scan %d", scan_id)
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "UPDATE scans SET status='failed', finished_at=?, error=? WHERE id=?",
            (now, str(exc), scan_id),
        )
        await db.commit()
```

Add `logger.info` at key points: scan start, scan complete, host count.

**Step 5: Commit**

```
fix: replace silent exceptions with structured logging
```

---

## Phase 2: Testing & Code Quality

### Task 5: Set up backend testing infrastructure

**Files:**
- Create: `backend/requirements-dev.txt`
- Create: `backend/conftest.py`
- Create: `backend/tests/__init__.py`

**Step 1: Create requirements-dev.txt**

```
-r requirements.txt
pytest==8.3.4
pytest-asyncio==0.24.0
httpx==0.28.1
ruff==0.8.6
mypy==1.14.1
```

**Step 2: Create conftest.py with in-memory DB fixture**

```python
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from main import app
from database import init_db, get_db


@pytest_asyncio.fixture
async def db():
    """In-memory SQLite database for testing."""
    import aiosqlite
    from database import SCHEMA

    conn = await aiosqlite.connect(":memory:")
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA foreign_keys=ON")
    await conn.executescript(SCHEMA)
    await conn.commit()
    yield conn
    await conn.close()


@pytest_asyncio.fixture
async def client(db):
    """Test client with overridden database."""
    async def override_get_db():
        return db

    # Patch get_db in all routers
    import routers.scans as scans_mod
    import routers.hosts as hosts_mod
    import routers.topology as topo_mod
    import routers.export as export_mod
    import services.scan_manager as scan_mod

    original_fns = {
        "scans": scans_mod.get_db,
        "hosts": hosts_mod.get_db,
        "topo": topo_mod.get_db,
        "export": export_mod.get_db,
        "scan_mgr": scan_mod.get_db,
    }

    scans_mod.get_db = override_get_db
    hosts_mod.get_db = override_get_db
    topo_mod.get_db = override_get_db
    export_mod.get_db = override_get_db
    scan_mod.get_db = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    # Restore
    scans_mod.get_db = original_fns["scans"]
    hosts_mod.get_db = original_fns["hosts"]
    topo_mod.get_db = original_fns["topo"]
    export_mod.get_db = original_fns["export"]
    scan_mod.get_db = original_fns["scan_mgr"]
```

**Step 3: Create tests/__init__.py (empty)**

**Step 4: Install dev deps and verify pytest discovers**

Run: `cd backend && pip install -r requirements-dev.txt && pytest --collect-only`
Expected: "no tests ran" (0 collected is fine — infrastructure works)

**Step 5: Commit**

```
feat: add backend testing infrastructure with pytest
```

---

### Task 6: Write backend tests for model validation

**Files:**
- Create: `backend/tests/test_models.py`

**Step 1: Write tests**

```python
import pytest
from pydantic import ValidationError
from models import ScanCreate


class TestScanCreateValidation:
    def test_valid_cidr(self):
        s = ScanCreate(target="192.168.1.0/24")
        assert s.target == "192.168.1.0/24"

    def test_valid_ip(self):
        s = ScanCreate(target="10.0.0.1")
        assert s.target == "10.0.0.1"

    def test_valid_hostname(self):
        s = ScanCreate(target="example.com")
        assert s.target == "example.com"

    def test_valid_subdomain(self):
        s = ScanCreate(target="sub.example.com")
        assert s.target == "sub.example.com"

    def test_strips_whitespace(self):
        s = ScanCreate(target="  10.0.0.1  ")
        assert s.target == "10.0.0.1"

    def test_rejects_command_injection(self):
        with pytest.raises(ValidationError):
            ScanCreate(target="192.168.1.0/24; rm -rf /")

    def test_rejects_pipe(self):
        with pytest.raises(ValidationError):
            ScanCreate(target="10.0.0.1 | cat /etc/passwd")

    def test_rejects_empty(self):
        with pytest.raises(ValidationError):
            ScanCreate(target="")

    def test_rejects_backtick(self):
        with pytest.raises(ValidationError):
            ScanCreate(target="`whoami`")

    def test_default_profile(self):
        s = ScanCreate(target="10.0.0.1")
        assert s.profile == "standard"

    def test_valid_profiles(self):
        for p in ("quick", "standard", "deep"):
            s = ScanCreate(target="10.0.0.1", profile=p)
            assert s.profile == p

    def test_invalid_profile(self):
        with pytest.raises(ValidationError):
            ScanCreate(target="10.0.0.1", profile="ultra")
```

**Step 2: Run tests**

Run: `cd backend && pytest tests/test_models.py -v`
Expected: All tests PASS

**Step 3: Commit**

```
test: add model validation tests
```

---

### Task 7: Write backend tests for API endpoints

**Files:**
- Create: `backend/tests/test_api.py`

**Step 1: Write endpoint tests**

```python
import pytest
import pytest_asyncio


@pytest.mark.asyncio
class TestScansAPI:
    async def test_create_scan_valid(self, client, db):
        # Mock execute_scan to not actually run nmap
        import routers.scans as scans_mod
        import asyncio
        original = scans_mod.execute_scan

        async def noop(*args):
            pass

        scans_mod.execute_scan = noop

        resp = await client.post("/api/scans", json={"target": "192.168.1.0/24", "profile": "quick"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["target"] == "192.168.1.0/24"
        assert data["profile"] == "quick"
        assert data["status"] == "pending"

        scans_mod.execute_scan = original

    async def test_create_scan_invalid_target(self, client):
        resp = await client.post("/api/scans", json={"target": "invalid; rm -rf /", "profile": "quick"})
        assert resp.status_code == 422

    async def test_list_scans_empty(self, client):
        resp = await client.get("/api/scans")
        assert resp.status_code == 200

    async def test_get_scan_not_found(self, client):
        resp = await client.get("/api/scans/999")
        assert resp.status_code == 404

    async def test_delete_scan_not_found(self, client):
        resp = await client.delete("/api/scans/999")
        assert resp.status_code == 404

    async def test_health(self, client):
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
```

**Step 2: Run tests**

Run: `cd backend && pytest tests/test_api.py -v`
Expected: All tests PASS

**Step 3: Commit**

```
test: add API endpoint tests
```

---

### Task 8: Write backend tests for topology logic

**Files:**
- Create: `backend/tests/test_topology.py`

**Step 1: Write topology tests**

```python
from topology.categorizer import _categorize_single
from topology.risk import _score_single
from topology.subnet import group_by_subnet, detect_gateways


class TestCategorizer:
    def test_server_with_http(self):
        host = {"ports": [{"port": 80}, {"port": 443}], "os_name": "Linux", "vendor": ""}
        assert _categorize_single(host) == "server"

    def test_workstation_windows(self):
        host = {"ports": [{"port": 3389}, {"port": 445}], "os_name": "Windows 10", "vendor": ""}
        assert _categorize_single(host) == "workstation"

    def test_printer_by_vendor(self):
        host = {"ports": [], "os_name": "", "vendor": "HP Inc"}
        assert _categorize_single(host) == "printer"

    def test_camera_by_vendor(self):
        host = {"ports": [], "os_name": "", "vendor": "Hikvision"}
        assert _categorize_single(host) == "camera"

    def test_network_device_by_vendor(self):
        host = {"ports": [], "os_name": "", "vendor": "Cisco Systems"}
        assert _categorize_single(host) == "network_device"

    def test_unknown_no_info(self):
        host = {"ports": [], "os_name": "", "vendor": ""}
        assert _categorize_single(host) == "unknown"


class TestRiskScoring:
    def test_no_risky_ports(self):
        host = {"ports": [{"port": 80}, {"port": 443}]}
        score, details = _score_single(host)
        assert score == 0.0
        assert details == []

    def test_telnet_high_risk(self):
        host = {"ports": [{"port": 23}]}
        score, details = _score_single(host)
        assert score == 3.0
        assert len(details) == 1

    def test_max_risk_cap(self):
        host = {"ports": [{"port": p} for p in [23, 21, 445, 3389, 6379, 27017, 514, 513, 512]]}
        score, _ = _score_single(host)
        assert score == 10.0

    def test_large_attack_surface(self):
        host = {"ports": [{"port": i} for i in range(1, 22)]}
        score, details = _score_single(host)
        assert any("attack surface" in d for d in details)


class TestSubnetGrouping:
    def test_groups_by_24(self):
        hosts = [
            {"ip": "192.168.1.10"},
            {"ip": "192.168.1.20"},
            {"ip": "192.168.2.5"},
        ]
        subnets = group_by_subnet(hosts)
        assert "192.168.1.0/24" in subnets
        assert "192.168.2.0/24" in subnets
        assert len(subnets["192.168.1.0/24"]) == 2

    def test_gateway_detection(self):
        hosts = [
            {"ip": "192.168.1.10", "subnet": "192.168.1.0/24",
             "traceroute": [{"ip": "10.0.0.1"}, {"ip": "192.168.1.1"}, {"ip": "192.168.1.10"}]},
            {"ip": "192.168.1.20", "subnet": "192.168.1.0/24",
             "traceroute": [{"ip": "10.0.0.1"}, {"ip": "192.168.1.1"}, {"ip": "192.168.1.20"}]},
        ]
        gws = detect_gateways(hosts)
        assert gws.get("192.168.1.0/24") == "192.168.1.1"
```

**Step 2: Run tests**

Run: `cd backend && pytest tests/test_topology.py -v`
Expected: All tests PASS

**Step 3: Commit**

```
test: add topology logic tests
```

---

### Task 9: Set up frontend testing infrastructure

**Files:**
- Modify: `frontend/package.json` (add devDependencies and scripts)
- Create: `frontend/vitest.config.ts`
- Create: `frontend/src/test-setup.ts`

**Step 1: Install test dependencies**

Run: `cd frontend && npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom`

**Step 2: Create vitest.config.ts**

```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test-setup.ts'],
    globals: true,
  },
});
```

**Step 3: Create src/test-setup.ts**

```typescript
import '@testing-library/jest-dom/vitest';
```

**Step 4: Add test scripts to package.json**

Add to `scripts`:
```json
"test": "vitest run",
"test:watch": "vitest"
```

**Step 5: Run to verify**

Run: `cd frontend && npx vitest run`
Expected: "No test files found" (infrastructure works)

**Step 6: Commit**

```
feat: add frontend testing infrastructure with vitest
```

---

### Task 10: Write frontend tests for utils and hooks

**Files:**
- Create: `frontend/src/utils/__tests__/formatters.test.ts`

**Step 1: Write formatter tests**

```typescript
import { describe, it, expect } from 'vitest';
import { riskColor, riskLabel, formatDuration } from '../formatters';

describe('riskColor', () => {
  it('returns red for critical risk', () => {
    expect(riskColor(8)).toBe('#ef4444');
  });
  it('returns amber for high risk', () => {
    expect(riskColor(5)).toBe('#f59e0b');
  });
  it('returns yellow for medium risk', () => {
    expect(riskColor(2)).toBe('#eab308');
  });
  it('returns green for low risk', () => {
    expect(riskColor(0)).toBe('#22c55e');
  });
});

describe('riskLabel', () => {
  it('returns Critical for >= 7', () => {
    expect(riskLabel(7)).toBe('Critical');
  });
  it('returns Low for 0', () => {
    expect(riskLabel(0)).toBe('Low');
  });
});

describe('formatDuration', () => {
  it('returns dash for null input', () => {
    expect(formatDuration(null, null)).toBe('\u2014');
  });
  it('formats seconds', () => {
    const start = '2024-01-01T00:00:00Z';
    const end = '2024-01-01T00:00:30Z';
    expect(formatDuration(start, end)).toBe('30s');
  });
  it('formats minutes and seconds', () => {
    const start = '2024-01-01T00:00:00Z';
    const end = '2024-01-01T00:02:15Z';
    expect(formatDuration(start, end)).toBe('2m 15s');
  });
});
```

**Step 2: Run tests**

Run: `cd frontend && npx vitest run`
Expected: All tests PASS

**Step 3: Commit**

```
test: add frontend util tests
```

---

### Task 11: Set up linting for both stacks

**Files:**
- Create: `backend/pyproject.toml`
- Create: `frontend/eslint.config.js`
- Modify: `frontend/package.json` (add lint scripts)

**Step 1: Create backend/pyproject.toml**

```toml
[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "A", "SIM"]

[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false
```

**Step 2: Install eslint for frontend**

Run: `cd frontend && npm install -D eslint @eslint/js typescript-eslint eslint-plugin-react-hooks`

**Step 3: Create frontend/eslint.config.js**

```javascript
import js from '@eslint/js';
import tseslint from 'typescript-eslint';
import reactHooks from 'eslint-plugin-react-hooks';

export default tseslint.config(
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    plugins: { 'react-hooks': reactHooks },
    rules: {
      ...reactHooks.configs.recommended.rules,
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    },
  },
  { ignores: ['dist/'] },
);
```

**Step 4: Add scripts to package.json**

```json
"lint": "eslint src/",
"typecheck": "tsc --noEmit"
```

**Step 5: Enable strict tsconfig**

In `frontend/tsconfig.json`, change:
```json
"noUnusedLocals": true,
"noUnusedParameters": true
```

**Step 6: Run linters and fix any issues**

Run: `cd backend && ruff check .`
Run: `cd frontend && npm run lint && npm run typecheck`
Fix any issues that arise.

**Step 7: Commit**

```
feat: add linting with ruff, mypy, eslint, and strict TypeScript
```

---

### Task 12: Fix TypeScript type safety issues

**Files:**
- Create: `frontend/src/hooks/useCytoscapeRef.ts`
- Modify: `frontend/src/pages/TopologyPage.tsx` (remove `as any`)
- Modify: `frontend/src/components/ExportButtons.tsx` (remove `as any`)
- Modify: `frontend/src/components/NetworkGraph.tsx` (expose cy via callback instead of DOM)
- Modify: `frontend/src/components/ScanLauncher.tsx` (fix `err: any`)
- Modify: `frontend/src/components/HostDetailPanel.tsx` (safe JSON.parse)

**Step 1: Create useCytoscapeRef hook**

Create `frontend/src/hooks/useCytoscapeRef.ts`:

```typescript
import { useRef, useCallback } from 'react';
import type cytoscape from 'cytoscape';

export function useCytoscapeRef() {
  const cyRef = useRef<cytoscape.Core | null>(null);

  const setCy = useCallback((cy: cytoscape.Core | null) => {
    cyRef.current = cy;
  }, []);

  return { cyRef, setCy };
}
```

**Step 2: Update NetworkGraph to call onCyInit callback**

Add `onCyInit?: (cy: cytoscape.Core | null) => void` to Props. Call `onCyInit(cy)` after initialization. Remove the DOM `__cy` assignment (the `useEffect` at line 59-64).

**Step 3: Update TopologyPage to use cyRef**

Replace `(container as any).__cy` with `cyRef.current` from the useCytoscapeRef hook.

**Step 4: Update ExportButtons to accept cy ref**

Change props to accept `cyRef: React.RefObject<cytoscape.Core | null>` instead of `graphContainerRef`.

**Step 5: Fix ScanLauncher error handling**

Change `catch (err: any)` to:
```typescript
} catch (err: unknown) {
  setError(err instanceof Error ? err.message : 'Unknown error');
}
```

**Step 6: Fix HostDetailPanel JSON.parse**

```typescript
const riskDetails = useMemo(() => {
  if (!host.risk_details) return [];
  try {
    return JSON.parse(host.risk_details) as string[];
  } catch {
    return [];
  }
}, [host.risk_details]);
```

**Step 7: Run typecheck**

Run: `cd frontend && npm run typecheck`
Expected: No errors

**Step 8: Commit**

```
fix: remove all 'as any' casts and improve type safety
```

---

## Phase 3: Performance & Architecture

### Task 13: Fix N+1 queries with shared host loader

**Files:**
- Create: `backend/services/host_loader.py`
- Modify: `backend/routers/hosts.py`
- Modify: `backend/routers/topology.py`
- Modify: `backend/routers/export.py`

**Step 1: Create host_loader.py with batched query**

```python
from __future__ import annotations

import logging
from typing import Any

import aiosqlite

logger = logging.getLogger(__name__)


async def load_hosts_with_data(db: aiosqlite.Connection, scan_id: int) -> list[dict[str, Any]]:
    """Load hosts with ports and traceroute using batched queries (avoids N+1)."""
    # Fetch all hosts
    cursor = await db.execute("SELECT * FROM hosts WHERE scan_id=?", (scan_id,))
    host_rows = await cursor.fetchall()
    if not host_rows:
        return []

    hosts_by_id: dict[int, dict[str, Any]] = {}
    for row in host_rows:
        h = dict(row)
        h["ports"] = []
        h["traceroute"] = []
        hosts_by_id[h["id"]] = h

    host_ids = list(hosts_by_id.keys())
    placeholders = ",".join("?" * len(host_ids))

    # Batch fetch ports
    cursor = await db.execute(
        f"SELECT host_id, port, protocol, state, service, version FROM ports WHERE host_id IN ({placeholders})",
        host_ids,
    )
    for row in await cursor.fetchall():
        r = dict(row)
        hid = r.pop("host_id")
        hosts_by_id[hid]["ports"].append(r)

    # Batch fetch traceroute
    cursor = await db.execute(
        f"SELECT host_id, hop, ip, rtt, hostname FROM traceroute_hops WHERE host_id IN ({placeholders}) ORDER BY hop",
        host_ids,
    )
    for row in await cursor.fetchall():
        r = dict(row)
        hid = r.pop("host_id")
        hosts_by_id[hid]["traceroute"].append(r)

    logger.debug("Loaded %d hosts with ports and traceroute for scan %d", len(hosts_by_id), scan_id)
    return list(hosts_by_id.values())
```

**Step 2: Update routers to use shared loader**

In `routers/hosts.py`, `routers/topology.py`, `routers/export.py`:
- Import `from services.host_loader import load_hosts_with_data`
- Replace all inline N+1 loops with `hosts = await load_hosts_with_data(db, scan_id)`
- Delete the duplicated `_load_hosts_with_data` from `topology.py`

**Step 3: Run tests**

Run: `cd backend && pytest -v`
Expected: All existing tests still pass

**Step 4: Commit**

```
perf: fix N+1 queries with batched host loader
```

---

### Task 14: Add pagination to scan listing

**Files:**
- Modify: `backend/routers/scans.py:39-47`
- Modify: `backend/models.py` (add PaginatedScans model)
- Modify: `frontend/src/api.ts`
- Modify: `frontend/src/pages/ScanPage.tsx`

**Step 1: Add pagination model**

In `backend/models.py`, add:

```python
class PaginatedScans(BaseModel):
    items: list[ScanOut]
    total: int
    skip: int
    limit: int
```

**Step 2: Update list_scans endpoint**

```python
from fastapi import Query

@router.get("", response_model=PaginatedScans)
async def list_scans(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200)) -> dict:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT COUNT(*) as cnt FROM scans")
        total = (await cursor.fetchone())["cnt"]

        cursor = await db.execute(
            "SELECT * FROM scans ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, skip),
        )
        rows = await cursor.fetchall()
        return {"items": [dict(r) for r in rows], "total": total, "skip": skip, "limit": limit}
    finally:
        await db.close()
```

**Step 3: Update frontend api.ts**

```typescript
listScans: (skip = 0, limit = 50) =>
  fetchJSON<{ items: Scan[]; total: number; skip: number; limit: number }>(
    `/scans?skip=${skip}&limit=${limit}`
  ),
```

Update `ScanPage.tsx` to use `.items` from the response:

```typescript
api.listScans().then((res) => setScans(res.items)).catch(console.error);
```

**Step 4: Run tests**

Run: `cd backend && pytest -v && cd ../frontend && npm run typecheck`

**Step 5: Commit**

```
feat: add pagination to scan listing
```

---

### Task 15: Add nmap timeout and concurrency limits

**Files:**
- Modify: `backend/scanner/profiles.py` (add timeout per profile)
- Modify: `backend/scanner/nmap_runner.py` (add timeout to subprocess)
- Modify: `backend/routers/scans.py` (add semaphore)

**Step 1: Add timeouts to profiles**

In `backend/scanner/profiles.py`, add `timeout` key to each profile dict:

```python
"quick": { ..., "timeout": 120 },
"standard": { ..., "timeout": 600 },
"deep": { ..., "timeout": 1800 },
```

Add helper:

```python
def get_profile_timeout(profile: str) -> int:
    if profile not in SCAN_PROFILES:
        raise ValueError(f"Unknown profile: {profile}")
    return SCAN_PROFILES[profile]["timeout"]
```

**Step 2: Add timeout to nmap_runner.py**

Update `run_nmap_scan` signature to accept `timeout: int = 600`. After reading stdout, wrap `process.wait()` with timeout:

```python
try:
    await asyncio.wait_for(process.wait(), timeout=timeout)
except asyncio.TimeoutError:
    process.kill()
    raise RuntimeError(f"nmap scan timed out after {timeout}s")
```

**Step 3: Add semaphore to scans router**

At module level in `backend/routers/scans.py`:

```python
_scan_semaphore = asyncio.Semaphore(3)
```

In `create_scan`, check before launching:

```python
if _scan_semaphore.locked():
    raise HTTPException(429, "Too many concurrent scans. Please wait.")
```

Wrap the `execute_scan` call to acquire semaphore inside the background task.

**Step 4: Commit**

```
feat: add nmap timeout and max 3 concurrent scans
```

---

### Task 16: Fix WebSocket broadcast and pure functions

**Files:**
- Modify: `backend/services/ws_manager.py:22-31`
- Modify: `backend/topology/subnet.py:8-20`

**Step 1: Use asyncio.gather for broadcast**

```python
import asyncio

async def broadcast(self, scan_id: int, data: dict) -> None:
    conns = self._connections.get(scan_id, [])
    if not conns:
        return
    payload = json.dumps(data)
    results = await asyncio.gather(
        *[ws.send_text(payload) for ws in conns],
        return_exceptions=True,
    )
    dead = [ws for ws, result in zip(conns, results) if isinstance(result, Exception)]
    for ws in dead:
        logger.warning("Removing dead WebSocket for scan %d", scan_id)
        conns.remove(ws)
```

**Step 2: Fix group_by_subnet to not mutate**

```python
def group_by_subnet(hosts: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Group hosts by their /24 subnet."""
    subnets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for host in hosts:
        ip = host.get("ip", "")
        try:
            network = ipaddress.ip_network(f"{ip}/24", strict=False)
            subnet_key = str(network)
        except ValueError:
            subnet_key = "unknown"
        enriched = {**host, "subnet": subnet_key}
        subnets[subnet_key].append(enriched)
    return dict(subnets)
```

Note: Callers that depend on `host["subnet"]` need to use the returned enriched hosts from the subnets dict.

**Step 3: Run tests**

Run: `cd backend && pytest -v`

**Step 4: Commit**

```
perf: concurrent WebSocket broadcast and pure subnet grouping
```

---

### Task 17: Add frontend search debounce and memoization

**Files:**
- Modify: `frontend/src/components/SearchBar.tsx`
- Modify: `frontend/src/components/HostDetailPanel.tsx`

**Step 1: Add debounce to SearchBar**

```typescript
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
```

**Step 2: Add useMemo to HostDetailPanel for riskDetails**

Already covered in Task 12.

**Step 3: Run typecheck and tests**

Run: `cd frontend && npm run typecheck && npx vitest run`

**Step 4: Commit**

```
perf: debounce search and memoize expensive computations
```

---

### Task 18: Use FastAPI dependency injection for database

**Files:**
- Modify: `backend/database.py` (add async generator)
- Modify: all routers (use `Depends`)
- Modify: `backend/conftest.py` (override dependency)

**Step 1: Add dependency-injectable get_db_dep**

In `backend/database.py`, add:

```python
from typing import AsyncGenerator

async def get_db_dep() -> AsyncGenerator[aiosqlite.Connection, None]:
    """FastAPI dependency that yields a DB connection."""
    db = await aiosqlite.connect(DATABASE_URL)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    try:
        yield db
    finally:
        await db.close()
```

**Step 2: Update all routers**

In each router, change from manual `get_db()` / `try/finally/close` to:

```python
from fastapi import Depends
from database import get_db_dep
import aiosqlite

@router.get("", ...)
async def list_scans(db: aiosqlite.Connection = Depends(get_db_dep)) -> ...:
    # No try/finally needed
    cursor = await db.execute(...)
    ...
```

**Step 3: Update conftest.py to override dependency**

Use `app.dependency_overrides[get_db_dep]` to inject the test database.

**Step 4: Run tests**

Run: `cd backend && pytest -v`

**Step 5: Commit**

```
refactor: use FastAPI dependency injection for database connections
```

---

## Phase 4: DevOps

### Task 19: Add CI/CD with GitHub Actions

**Files:**
- Create: `.github/workflows/ci.yml`

**Step 1: Create workflow**

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  backend:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: backend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: pip
      - run: pip install -r requirements-dev.txt
      - run: ruff check .
      - run: mypy . --ignore-missing-imports
      - run: pytest -v

  frontend:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
          cache-dependency-path: frontend/package-lock.json
      - run: npm ci
      - run: npm run lint
      - run: npm run typecheck
      - run: npm test
```

**Step 2: Commit**

```
feat: add GitHub Actions CI for lint, typecheck, and tests
```

---

### Task 20: Add missing config files and Docker improvements

**Files:**
- Create: `.dockerignore`
- Create: `.env.example`
- Create: `.editorconfig`
- Modify: `docker-compose.yml` (healthchecks, resource limits)

**Step 1: Create .dockerignore**

```
.git
.github
.claude
.env
.env.*
node_modules
__pycache__
*.pyc
*.db
*.sqlite
dist
docs
*.md
!README.md
.vscode
.idea
```

**Step 2: Create .env.example**

```bash
# Backend
DATABASE_URL=netvista.db
HOST=0.0.0.0
PORT=8040
NMAP_PATH=nmap
DATA_DIR=/data
CORS_ORIGINS=http://localhost:5175
LOG_LEVEL=INFO
```

**Step 3: Create .editorconfig**

```ini
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
indent_style = space
indent_size = 2

[*.py]
indent_size = 4

[*.md]
trim_trailing_whitespace = false
```

**Step 4: Update docker-compose.yml**

```yaml
services:
  backend:
    build: ./backend
    container_name: netvista-api
    network_mode: host
    cap_add:
      - NET_RAW
      - NET_ADMIN
    volumes:
      - netvista-data:/data
    environment:
      - DATABASE_URL=/data/netvista.db
      - HOST=0.0.0.0
      - PORT=8040
      - CORS_ORIGINS=http://localhost:5175
      - LOG_LEVEL=INFO
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 1G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8040/api/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s

  frontend:
    build: ./frontend
    container_name: netvista-frontend
    ports:
      - "5175:80"
    depends_on:
      backend:
        condition: service_healthy
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:80"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 5s

volumes:
  netvista-data:
```

**Step 5: Commit**

```
feat: add config files, Docker healthchecks, and resource limits
```

---

## Phase 5: UX & Polish

### Task 21: Add Error Boundary component

**Files:**
- Create: `frontend/src/components/ErrorBoundary.tsx`
- Modify: `frontend/src/main.tsx` (wrap App)

**Step 1: Create ErrorBoundary**

```typescript
import { Component, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback ?? (
          <div className="min-h-screen flex items-center justify-center bg-gray-950 text-white">
            <div className="text-center p-8">
              <h1 className="text-2xl font-bold text-red-400 mb-4">Something went wrong</h1>
              <p className="text-gray-400 mb-4">{this.state.error?.message}</p>
              <button
                onClick={() => window.location.reload()}
                className="bg-cyan-600 hover:bg-cyan-500 px-4 py-2 rounded text-sm"
              >
                Reload
              </button>
            </div>
          </div>
        )
      );
    }
    return this.props.children;
  }
}
```

**Step 2: Wrap App in main.tsx**

```typescript
import { ErrorBoundary } from './components/ErrorBoundary';

// In render:
<ErrorBoundary>
  <BrowserRouter>
    <App />
  </BrowserRouter>
</ErrorBoundary>
```

**Step 3: Commit**

```
feat: add ErrorBoundary for graceful error handling
```

---

### Task 22: Add accessibility improvements

**Files:**
- Modify: `frontend/src/components/ScanLauncher.tsx` (ARIA labels)
- Modify: `frontend/src/pages/TopologyPage.tsx` (semantic HTML, aria-live)
- Modify: `frontend/src/pages/ScanPage.tsx` (semantic HTML)

**Step 1: ScanLauncher — add id to input and htmlFor to label**

Add `id="scan-target"` to the target input and `htmlFor="scan-target"` to the label. Add `aria-describedby="scan-error"` when error is present.

**Step 2: TopologyPage — add aria-live to loading/error**

Add `role="status" aria-live="polite"` to the loading and error overlays. Wrap page content in `<main>`.

**Step 3: ScanPage — semantic HTML**

Wrap in `<main>`, use `<section>` for ScanLauncher and ScanHistory areas.

**Step 4: Run typecheck**

Run: `cd frontend && npm run typecheck`

**Step 5: Commit**

```
feat: add ARIA labels and semantic HTML for accessibility
```

---

### Task 23: Harden nginx configuration

**Files:**
- Modify: `frontend/nginx.conf`

**Step 1: Update nginx.conf**

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml;
    gzip_min_length 1024;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self' ws: wss:;" always;

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2?)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /api {
        proxy_pass http://host.docker.internal:8040;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 3600;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

**Step 2: Commit**

```
feat: harden nginx with security headers, gzip, and caching
```

---

### Task 24: Final review and README update

**Files:**
- Verify: `README.md` reflects actual project state after all changes.

**Step 1: Review README accuracy**

Read `README.md` and verify all commands, paths, and descriptions match the actual code after all improvements.

**Step 2: Final commit**

```
docs: update README and design docs for v0.2.0
```

---

## Summary

| Phase | Tasks | Key Changes |
|-------|-------|-------------|
| 1. Security | 1-4 | Input validation, CORS, Docker non-root, logging |
| 2. Testing | 5-12 | pytest, vitest, linting, TypeScript strict, type safety |
| 3. Performance | 13-18 | N+1 fix, pagination, timeouts, debounce, DI |
| 4. DevOps | 19-20 | GitHub Actions CI, Docker healthchecks, config files |
| 5. UX | 21-24 | ErrorBoundary, a11y, nginx hardening, README |

**Total: 24 tasks, ~24 commits**
