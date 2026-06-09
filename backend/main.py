from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers import scans, hosts, topology, export
from services.scan_manager import fail_orphaned_scans


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await fail_orphaned_scans()
    yield


app = FastAPI(
    title="NetVista",
    description="Network Topology Auto-Mapper",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # Credentials cannot be combined with a wildcard origin (browsers reject it),
    # and NetVista uses no cookies/auth, so credentials stay off.
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scans.router)
app.include_router(hosts.router)
app.include_router(topology.router)
app.include_router(export.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "netvista"}
