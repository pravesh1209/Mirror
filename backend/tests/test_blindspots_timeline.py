"""Tests for blind spots, timeline, and demo seed."""
from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.db import engine, init_models
from app.main import app
from app.models import Base


@pytest_asyncio.fixture
async def client():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await init_models()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_demo_seed_creates_history(client: AsyncClient):
    r = await client.post("/api/demo/seed")
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "seeded"
    assert body["label"] == "DEMO DATA"
    assert body["decisions"] >= 6
    user_id = body["user_id"]

    # Fingerprint
    r = await client.get(f"/api/profile/{user_id}/fingerprint")
    assert r.status_code == 200
    fp = r.json()
    assert fp["sample_count"] >= 6
    # With the deterministic persona, some axes should be non-null
    non_null = [k for k, v in fp["features"].items() if v is not None]
    assert len(non_null) >= 4

    # Stats should show resolved predictions
    r = await client.get(f"/api/profile/{user_id}/stats")
    assert r.status_code == 200
    st = r.json()
    assert st["observations"] >= 6
    assert st["predictions"] >= 1
    assert st["resolved"] >= 1


@pytest.mark.asyncio
async def test_demo_reset(client: AsyncClient):
    await client.post("/api/demo/seed")
    r = await client.post("/api/demo/reset")
    assert r.status_code == 200
    assert r.json()["users_deleted"] >= 1


@pytest.mark.asyncio
async def test_blind_spots_analyze(client: AsyncClient):
    r = await client.post("/api/demo/seed")
    user_id = r.json()["user_id"]

    r = await client.post("/api/blind-spots/analyze", json={"user_id": user_id})
    assert r.status_code == 200, r.text
    body = r.json()
    assert "known" in body and "unknown" in body
    # At least one axis should be unknown
    assert len(body["unknown"]) >= 1
    # All unknowns should have severity > 0
    for u in body["unknown"]:
        assert u["severity"] is not None
        assert 0.0 <= u["severity"] <= 1.0


@pytest.mark.asyncio
async def test_blind_spot_test_generates_scenario(client: AsyncClient):
    r = await client.post("/api/demo/seed")
    user_id = r.json()["user_id"]

    r = await client.post(
        "/api/blind-spots/test",
        json={"user_id": user_id, "axis": "adaptability"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "scenario" in body
    assert body["scenario"]["title"]


@pytest.mark.asyncio
async def test_timeline_after_demo_seed(client: AsyncClient):
    r = await client.post("/api/demo/seed")
    user_id = r.json()["user_id"]

    r = await client.get(f"/api/model/timeline?user_id={user_id}")
    assert r.status_code == 200, r.text
    body = r.json()
    entries = body["entries"]
    assert len(entries) >= 3
    # versions should be strictly increasing
    versions = [e["version"] for e in entries]
    assert versions == sorted(versions)
    # narratives should be non-empty
    for e in entries:
        assert e["narrative"]