import pytest


@pytest.mark.asyncio
class TestScansAPI:
    async def test_create_scan_valid(self, client, db):
        import routers.scans as scans_mod

        original = scans_mod.execute_scan

        async def noop(*args):
            pass

        scans_mod.execute_scan = noop
        try:
            resp = await client.post(
                "/api/scans",
                json={"target": "192.168.1.0/24", "profile": "quick"},
            )
            assert resp.status_code == 201
            data = resp.json()
            assert data["target"] == "192.168.1.0/24"
            assert data["profile"] == "quick"
            assert data["status"] == "pending"
        finally:
            scans_mod.execute_scan = original

    async def test_create_scan_invalid_target(self, client):
        resp = await client.post(
            "/api/scans",
            json={"target": "invalid; rm -rf /", "profile": "quick"},
        )
        assert resp.status_code == 422

    async def test_list_scans_empty(self, client):
        resp = await client.get("/api/scans")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["skip"] == 0
        assert data["limit"] == 50

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
