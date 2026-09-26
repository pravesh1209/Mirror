"""End-to-end calibration flow over HTTP."""
from __future__ import annotations

import uuid

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


def _event(etype: str, t: int, opt: str | None = None, payload: dict | None = None) -> dict:
    return {
        "event_id": uuid.uuid4().hex,
        "event_type": etype,
        "option_id": opt,
        "payload": payload or {},
        "relative_time_ms": t,
        "client_ts": None,
    }


@pytest.mark.asyncio
async def test_full_calibration_flow(client: AsyncClient):
    # 1. Create a session
    r = await client.post("/api/sessions", json={"display_name": "Test", "mode": "live"})
    assert r.status_code == 201, r.text
    sess = r.json()
    session_id = sess["session_id"]
    user_id = sess["user_id"]
    assert sess["ai_status"]["provider"] in {"null", "deepseek"}

    # 2. Generate a scenario (bank only, deterministic)
    r = await client.post(
        "/api/scenarios/generate",
        json={"session_id": session_id, "use_bank_only": True},
    )
    assert r.status_code == 201, r.text
    scenario = r.json()["scenario"]
    scenario_id = scenario["id"]
    assert scenario["source"] == "seed"
    assert len(scenario["options"]) >= 2

    # 3. GET the scenario back — must be identical
    r = await client.get(f"/api/scenarios/{scenario_id}")
    assert r.status_code == 200
    assert r.json()["id"] == scenario_id

    # 4. Post events
    opt_ids = [o["id"] for o in scenario["options"]]
    first_opt = opt_ids[0]
    second_opt = opt_ids[1] if len(opt_ids) > 1 else first_opt

    events = [
        _event("scenario_started", 0),
        _event("option_viewed", 500, first_opt),
        _event("option_viewed", 1200, second_opt),
        _event("information_opened", 1600, None, {"info_id": "i1"}),
        _event("decision_changed", 2200, first_opt),
        _event("decision_submitted", 3000, first_opt),
        _event("scenario_completed", 3000),
    ]
    r = await client.post(
        f"/api/scenarios/{scenario_id}/events",
        json={"session_id": session_id, "events": events},
    )
    assert r.status_code == 202, r.text
    assert r.json()["accepted"] == len(events)

    # 5. Re-post the same events — should be all duplicates
    r = await client.post(
        f"/api/scenarios/{scenario_id}/events",
        json={"session_id": session_id, "events": events},
    )
    assert r.status_code == 202
    assert r.json()["accepted"] == 0
    assert r.json()["duplicates_ignored"] == len(events)

    # 6. Submit the decision
    r = await client.post(
        f"/api/scenarios/{scenario_id}/decision",
        json={
            "session_id": session_id,
            "final_option_id": first_opt,
            "self_confidence": 0.7,
        },
    )
    assert r.status_code == 200, r.text
    decision = r.json()
    assert decision["derived"]["decision_latency_ms"] == 3000
    assert decision["derived"]["unique_options_viewed"] == 2
    assert decision["derived"]["reversal_count"] == 1
    assert decision["derived"]["info_items_opened"] == 1
    assert decision["profile_version"] >= 1

    # 7. Submitting again must 409
    r = await client.post(
        f"/api/scenarios/{scenario_id}/decision",
        json={"session_id": session_id, "final_option_id": first_opt},
    )
    assert r.status_code == 409

    # 8. Fingerprint
    r = await client.get(f"/api/profile/{user_id}/fingerprint")
    assert r.status_code == 200, r.text
    fp = r.json()
    assert fp["sample_count"] == 1
    assert fp["version"] >= 1
    assert set(fp["features"].keys()) >= {
        "decision_speed", "exploration", "risk_tolerance",
        "evidence_seeking", "reconsideration", "consistency",
        "novelty_seeking", "uncertainty_tolerance", "adaptability",
    }
    # With 1 sample, most features should be null or low-confidence
    assert "adaptability" in fp["insufficient"]

    # 9. Stats
    r = await client.get(f"/api/profile/{user_id}/stats")
    assert r.status_code == 200
    stats = r.json()
    assert stats["observations"] == 1
    assert stats["predictions"] == 0
    assert stats["calibration_available"] is False

    # 10. Second scenario for a slightly richer profile
    r = await client.post(
        "/api/scenarios/generate",
        json={"session_id": session_id, "use_bank_only": True},
    )
    assert r.status_code == 201
    sc2 = r.json()["scenario"]
    assert sc2["id"] != scenario_id

    # 11. Complete scenario 2
    opt2 = sc2["options"][0]["id"]
    events2 = [
        _event("scenario_started", 0),
        _event("option_viewed", 400, opt2),
        _event("decision_submitted", 800, opt2),
        _event("scenario_completed", 800),
    ]
    r = await client.post(
        f"/api/scenarios/{sc2['id']}/events",
        json={"session_id": session_id, "events": events2},
    )
    assert r.status_code == 202

    r = await client.post(
        f"/api/scenarios/{sc2['id']}/decision",
        json={"session_id": session_id, "final_option_id": opt2},
    )
    assert r.status_code == 200

    r = await client.get(f"/api/profile/{user_id}/fingerprint")
    assert r.status_code == 200
    fp2 = r.json()
    assert fp2["sample_count"] == 2
    assert fp2["version"] >= 2

    # 12. Bank endpoint
    r = await client.get("/api/scenarios/bank")
    assert r.status_code == 200
    assert r.json()["count"] == 12

    # 13. Delete user
    r = await client.delete(f"/api/profile/{user_id}")
    assert r.status_code == 204

    r = await client.get(f"/api/profile/{user_id}/fingerprint")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_scenario_generate_missing_session(client: AsyncClient):
    r = await client.post(
        "/api/scenarios/generate",
        json={"session_id": "does-not-exist", "use_bank_only": True},
    )
    assert r.status_code == 404
    body = r.json()
    assert body["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_unknown_scenario_404(client: AsyncClient):
    r = await client.get("/api/scenarios/nope")
    assert r.status_code == 404