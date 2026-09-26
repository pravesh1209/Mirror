"""End-to-end prediction loop test."""
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


async def _complete_scenario(
    client: AsyncClient,
    session_id: str,
    *,
    preferred_attr: str,
    reverse: bool = False,
) -> dict:
    """Complete one scenario choosing the option that maximizes `preferred_attr`."""
    r = await client.post(
        "/api/scenarios/generate",
        json={"session_id": session_id, "use_bank_only": True},
    )
    assert r.status_code == 201, r.text
    sc = r.json()["scenario"]

    def attr_of(o, key):
        return o["attributes"][key]

    best = max(sc["options"], key=lambda o: attr_of(o, preferred_attr))
    second = sorted(sc["options"], key=lambda o: attr_of(o, preferred_attr), reverse=True)[1]

    t0 = 0
    events = [_event("scenario_started", t0)]
    order = [best, second] if not reverse else [second, best]
    t = 500
    for o in order:
        events.append(_event("option_viewed", t, o["id"]))
        t += 700
    events.append(_event("information_opened", t, None, {"info_id": "i1"}))
    t += 500
    events.append(_event("decision_submitted", t, best["id"]))
    events.append(_event("scenario_completed", t))

    r = await client.post(
        f"/api/scenarios/{sc['id']}/events",
        json={"session_id": session_id, "events": events},
    )
    assert r.status_code == 202, r.text

    r = await client.post(
        f"/api/scenarios/{sc['id']}/decision",
        json={"session_id": session_id, "final_option_id": best["id"]},
    )
    assert r.status_code == 200, r.text
    return {"scenario": sc, "decision": r.json(), "chosen_label": best["label"]}


@pytest.mark.asyncio
async def test_prediction_requires_profile(client: AsyncClient):
    r = await client.post("/api/sessions", json={"mode": "live"})
    user_id = r.json()["user_id"]
    session_id = r.json()["session_id"]

    r = await client.post(
        "/api/scenarios/generate",
        json={"session_id": session_id, "use_bank_only": True},
    )
    sc_id = r.json()["scenario"]["id"]

    # No decisions yet
    r = await client.post(
        "/api/predictions",
        json={"user_id": user_id, "scenario_id": sc_id},
    )
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "NO_PROFILE"


@pytest.mark.asyncio
async def test_full_prediction_resolve_loop(client: AsyncClient):
    # session
    r = await client.post("/api/sessions", json={"display_name": "T", "mode": "live"})
    session_id = r.json()["session_id"]
    user_id = r.json()["user_id"]

    # Complete 3 scenarios preferring high reward
    for i in range(3):
        await _complete_scenario(client, session_id, preferred_attr="reward")

    # Fingerprint should show some signals now
    r = await client.get(f"/api/profile/{user_id}/fingerprint")
    assert r.status_code == 200
    fp = r.json()
    assert fp["sample_count"] == 3

    # Generate a new scenario to predict on
    r = await client.post(
        "/api/scenarios/generate",
        json={"session_id": session_id, "use_bank_only": True},
    )
    sc = r.json()["scenario"]

    # Predict
    r = await client.post(
        "/api/predictions",
        json={"user_id": user_id, "scenario_id": sc["id"]},
    )
    assert r.status_code == 201, r.text
    pred = r.json()
    assert pred["predicted_final_option"]["label"] in {o["label"] for o in sc["options"]}
    assert 0.0 <= pred["confidence"] <= 1.0
    assert pred["narrative_source"] in {"llm", "template"}
    assert len(pred["evidence"]) >= 1
    assert "high" in pred["confidence_bands"]

    # Complete the scenario — pick the SAME option MIRROR predicted so we get a hit
    predicted_label = pred["predicted_final_option"]["label"]
    chosen = next(o for o in sc["options"] if o["label"] == predicted_label)
    events = [
        _event("scenario_started", 0),
        _event("option_viewed", 400, chosen["id"]),
        _event("decision_submitted", 1200, chosen["id"]),
        _event("scenario_completed", 1200),
    ]
    r = await client.post(
        f"/api/scenarios/{sc['id']}/events",
        json={"session_id": session_id, "events": events},
    )
    assert r.status_code == 202

    r = await client.post(
        f"/api/scenarios/{sc['id']}/decision",
        json={"session_id": session_id, "final_option_id": chosen["id"]},
    )
    assert r.status_code == 200
    decision_id = r.json()["decision_id"]

    # Resolve
    r = await client.post(
        f"/api/predictions/{pred['prediction_id']}/resolve",
        json={"decision_id": decision_id},
    )
    assert r.status_code == 200, r.text
    res = r.json()
    assert res["metrics"]["choice_correct"] is True
    assert len(res["rows"]) >= 3
    assert res["error_analysis"] is None  # correct prediction, no reflection

    # Resolve again -> 409
    r = await client.post(
        f"/api/predictions/{pred['prediction_id']}/resolve",
        json={"decision_id": decision_id},
    )
    assert r.status_code == 409

    # Stats reflect the resolved prediction
    r = await client.get(f"/api/profile/{user_id}/stats")
    assert r.status_code == 200
    st = r.json()
    assert st["observations"] == 4
    assert st["predictions"] == 1
    assert st["resolved"] == 1
    assert st["correct"] == 1
    assert st["choice_accuracy"] == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_miss_produces_reflection(client: AsyncClient):
    r = await client.post("/api/sessions", json={"mode": "live"})
    session_id = r.json()["session_id"]
    user_id = r.json()["user_id"]

    # Build a small profile
    for _ in range(2):
        await _complete_scenario(client, session_id, preferred_attr="reward")

    # Predict on a new scenario
    r = await client.post(
        "/api/scenarios/generate",
        json={"session_id": session_id, "use_bank_only": True},
    )
    sc = r.json()["scenario"]
    r = await client.post(
        "/api/predictions",
        json={"user_id": user_id, "scenario_id": sc["id"]},
    )
    pred = r.json()
    predicted_label = pred["predicted_final_option"]["label"]

    # Deliberately pick a DIFFERENT option
    other = next(o for o in sc["options"] if o["label"] != predicted_label)

    events = [
        _event("scenario_started", 0),
        _event("option_viewed", 400, other["id"]),
        _event("decision_submitted", 1200, other["id"]),
        _event("scenario_completed", 1200),
    ]
    r = await client.post(
        f"/api/scenarios/{sc['id']}/events",
        json={"session_id": session_id, "events": events},
    )
    assert r.status_code == 202
    r = await client.post(
        f"/api/scenarios/{sc['id']}/decision",
        json={"session_id": session_id, "final_option_id": other["id"]},
    )
    decision_id = r.json()["decision_id"]

    r = await client.post(
        f"/api/predictions/{pred['prediction_id']}/resolve",
        json={"decision_id": decision_id},
    )
    assert r.status_code == 200, r.text
    res = r.json()
    assert res["metrics"]["choice_correct"] is False
    assert res["error_analysis"] is not None
    assert res["error_analysis"]["failed_assumption"]
    assert res["error_analysis"]["model_update"]


@pytest.mark.asyncio
async def test_whatif_shifts_prediction(client: AsyncClient):
    r = await client.post("/api/sessions", json={"mode": "live"})
    session_id = r.json()["session_id"]
    user_id = r.json()["user_id"]

    for _ in range(2):
        await _complete_scenario(client, session_id, preferred_attr="reward")

    r = await client.post(
        "/api/scenarios/generate",
        json={"session_id": session_id, "use_bank_only": True},
    )
    sc = r.json()["scenario"]
    r = await client.post(
        "/api/predictions",
        json={"user_id": user_id, "scenario_id": sc["id"]},
    )
    pred = r.json()

    r = await client.post(
        f"/api/predictions/{pred['prediction_id']}/whatif",
        json={"overrides": {"time_pressure": 0.95}},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["previous_final"]
    assert body["new_final"]
    assert "time_pressure" in body["reason"]
    assert isinstance(body["delta_confidence"], float)