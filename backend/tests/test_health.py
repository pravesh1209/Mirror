"""Smoke tests for health & status endpoints."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "version" in body


@pytest.mark.asyncio
async def test_status():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/status")
    assert r.status_code == 200
    body = r.json()
    assert body["db"] == "ok"
    assert "ai" in body
    assert body["ai"]["provider"] in {"null", "deepseek"}
