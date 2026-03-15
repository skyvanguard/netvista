import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from main import app
from database import SCHEMA


@pytest_asyncio.fixture
async def db():
    """In-memory SQLite database for testing."""
    import aiosqlite

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

    scans_mod.get_db = original_fns["scans"]
    hosts_mod.get_db = original_fns["hosts"]
    topo_mod.get_db = original_fns["topo"]
    export_mod.get_db = original_fns["export"]
    scan_mod.get_db = original_fns["scan_mgr"]
