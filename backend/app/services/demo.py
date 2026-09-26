"""Deterministic demo user.

Completes a fixed set of bank scenarios with a fixed persona so that
the profile, fingerprint, and prediction history are ready to show
immediately. Zero API calls are required.
"""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Event, Prediction, PredictionResult, User
from ..models import Decision
from ..models import Session as SessionModel
from ..services.decisions import submit_decision
from ..services.predictions import create_prediction, resolve_prediction
from ..services.scenarios import generate_scenario
from ..simulation.fallback_bank import all_scenarios
from ..schemas import DecisionRequest, PredictionRequest, ResolveRequest

log = logging.getLogger("mirror.services.demo")

DEMO_DISPLAY_NAME = "DEMO DATA"

# Each entry: how many times to complete a scenario choosing which option.
# Persona: "cautious explorer" — prefers info_availability and low risk.
_SEQUENCE = [
    # bank scenario index, choice strategy
    (0, "low_risk"),      # getting across town
    (1, "high_info"),     # last-minute dinner
    (2, "high_info"),     # purchase
    (4, "high_info"),     # study
    (5, "low_risk"),      # course opp (reveal)
    (7, "high_info"),     # job offers
    (8, "high_info"),     # internal move (reveal)
    (9, "low_risk"),      # $500
    (11, "high_info"),    # too many threads
]


def _pick_option(options: list[dict], strategy: str) -> dict:
    key = {
        "low_risk": "risk",
        "high_info": "info_availability",
        "high_reward": "reward",
    }.get(strategy, "info_availability")

    if strategy == "low_risk":
        return min(options, key=lambda o: o["attributes"][key])
    return max(options, key=lambda o: o["attributes"][key])


async def seed_demo(db: AsyncSession) -> dict:
    """Create a demo user with a deterministic history. Returns ids."""
    user = User(display_name=DEMO_DISPLAY_NAME, is_demo=True)
    db.add(user)
    await db.flush()

    sess = SessionModel(user_id=user.id, mode="demo", ai_provider="null")
    db.add(sess)
    await db.flush()

    used_titles: set[str] = set()
    decisions_made = 0
    prediction_ids: list[str] = []
    resolution_ids: list[str] = []

    for idx, strategy in _SEQUENCE:
        try:
            sc_out = await generate_scenario(
                db, session_id=sess.id, use_bank_only=True
            )
        except Exception:
            log.exception("demo scenario generation failed at step %s", idx)
            continue

        opts = [
            {
                "id": o.id,
                "label": o.label,
                "attributes": {
                    "risk": o.attributes.risk,
                    "time_cost": o.attributes.time_cost,
                    "money_cost": o.attributes.money_cost,
                    "novelty": o.attributes.novelty,
                    "uncertainty": o.attributes.uncertainty,
                    "info_availability": o.attributes.info_availability,
                    "reward": o.attributes.reward,
                },
            }
            for o in sc_out.options
        ]
        chosen = _pick_option(opts, strategy)
        used_titles.add(sc_out.title)

        # Fake event stream — realistic timing
        from ..models import Event as EventModel  # local to avoid circular import at module load
        import uuid

        t0 = 0
        events = [
            EventModel(
                event_id=uuid.uuid4().hex,
                session_id=sess.id,
                scenario_id=sc_out.id,
                event_type="scenario_started",
                option_id=None,
                payload={},
                relative_time_ms=t0,
            ),
            EventModel(
                event_id=uuid.uuid4().hex,
                session_id=sess.id,
                scenario_id=sc_out.id,
                event_type="option_viewed",
                option_id=opts[0]["id"],
                payload={},
                relative_time_ms=500,
            ),
        ]
        if len(opts) > 1:
            events.append(
                EventModel(
                    event_id=uuid.uuid4().hex,
                    session_id=sess.id,
                    scenario_id=sc_out.id,
                    event_type="option_viewed",
                    option_id=opts[1]["id"],
                    payload={},
                    relative_time_ms=1200,
                )
            )
        events.append(
            EventModel(
                event_id=uuid.uuid4().hex,
                session_id=sess.id,
                scenario_id=sc_out.id,
                event_type="information_opened",
                option_id=None,
                payload={"info_id": f"info_{idx}"},
                relative_time_ms=1600,
            )
        )
        events.append(
            EventModel(
                event_id=uuid.uuid4().hex,
                session_id=sess.id,
                scenario_id=sc_out.id,
                event_type="decision_submitted",
                option_id=chosen["id"],
                payload={},
                relative_time_ms=2600,
            )
        )
        events.append(
            EventModel(
                event_id=uuid.uuid4().hex,
                session_id=sess.id,
                scenario_id=sc_out.id,
                event_type="scenario_completed",
                option_id=None,
                payload={},
                relative_time_ms=2600,
            )
        )
        db.add_all(events)
        await db.flush()

        try:
            dec = await submit_decision(
                db,
                scenario_id=sc_out.id,
                req=DecisionRequest(
                    session_id=sess.id,
                    final_option_id=chosen["id"],
                    self_confidence=0.65,
                ),
            )
        except Exception:
            log.exception("demo decision failed at step %s", idx)
            continue
        decisions_made += 1

        # For the last two decisions, also create and resolve a prediction so
        # the dashboard has non-zero accuracy on first view.
        if idx >= 7:
            try:
                pred = await create_prediction(
                    db,
                    PredictionRequest(user_id=user.id, scenario_id=sc_out.id),
                )
                prediction_ids.append(pred.prediction_id)
                res = await resolve_prediction(
                    db,
                    prediction_id=pred.prediction_id,
                    decision_id=dec.decision_id,
                )
                resolution_ids.append(res.prediction_id)
            except Exception:
                log.exception("demo prediction failed at step %s", idx)

    await db.flush()

    return {
        "user_id": user.id,
        "session_id": sess.id,
        "decisions": decisions_made,
        "predictions": prediction_ids,
        "resolved": resolution_ids,
    }


async def reset_demo(db: AsyncSession) -> int:
    """Delete all users flagged is_demo and cascade. Returns rows deleted."""
    q = await db.execute(select(User).where(User.is_demo.is_(True)))
    users = list(q.scalars().all())
    for u in users:
        await db.delete(u)
    await db.flush()
    return len(users)


__all__ = ["seed_demo", "reset_demo", "DEMO_DISPLAY_NAME"]