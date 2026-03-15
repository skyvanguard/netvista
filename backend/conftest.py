import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from database import SCHEMA, get_db_dep
from main import app


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
    async def override():
        yield db

    app.dependency_overrides[get_db_dep] = override

    # Still need to patch scan_manager since it uses get_db() directly
    import services.scan_manager as scan_mod

    original_scan_get_db = scan_mod.get_db

    async def override_get_db():
        return db

    scan_mod.get_db = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()
    scan_mod.get_db = original_scan_get_db
