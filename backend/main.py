import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth import verify_api_key
from config import API_KEY
from database import init_db
from logging_config import setup_logging
from routers import export, hosts, scans, topology
from services.scan_manager import fail_orphaned_scans

log = logging.getLogger("netvista")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    log.info("NetVista starting (auth %s)", "enabled" if API_KEY else "disabled")
    await init_db()
    await fail_orphaned_scans()
    yield


app = FastAPI(
    title="NetVista",
    description="Network Topology Auto-Mapper",
    version="0.3.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # Auth (when enabled) is a header/query API key, not cookies, so credentials
    # stay off — which is also required since combining them with a wildcard
    # origin is rejected by browsers.
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API-key auth (no-op unless API_KEY is set). The scans router applies it
# per-endpoint instead, so its WebSocket can authenticate via query param.
_auth = [Depends(verify_api_key)]
app.include_router(scans.router)
app.include_router(hosts.router, dependencies=_auth)
app.include_router(topology.router, dependencies=_auth)
app.include_router(export.router, dependencies=_auth)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "netvista"}
