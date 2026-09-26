"""Event ingest and decision submission.

Event ingest is idempotent on client-supplied event_id.
Decision submission recomputes the user's behavior profile.
"""
from __future__ import annotations

import logging

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..behavior.events import metrics_from_events
from ..behavior.profile import compute_for_user, persist_profile
from ..models import Decision, Event, Scenario, ScenarioOption
from ..models import Session as SessionModel
from ..schemas import (
    DecisionDerived,
    DecisionRequest,
    DecisionResponse,
    EventsBatchRequest,
    EventsBatchResponse,
)

log = logging.getLogger("mirror.services.decisions")


async def ingest_events(
    db: AsyncSession,
    *,
    scenario_id: str,
    req: EventsBatchRequest,
) -> EventsBatchResponse:
    sc = await db.get(Scenario, scenario_id)
    if sc is None:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "scenario not found"})

    sess = await db.get(SessionModel, req.session_id)
    if sess is None:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "session not found"})

    ids = [e.event_id for e in req.events]
    if not ids:
        return EventsBatchResponse(accepted=0, duplicates_ignored=0)

    existing_q = await db.execute(select(Event.event_id).where(Event.event_id.in_(ids)))
    existing = set(existing_q.scalars().all())

    accepted = 0
    dup = 0
    for e in req.events:
        if e.event_id in existing:
            dup += 1
            continue
        db.add(
            Event(
                event_id=e.event_id,
                session_id=req.session_id,
                scenario_id=scenario_id,
                event_type=e.event_type,
                option_id=e.option_id,
                payload=e.payload or {},
                relative_time_ms=e.relative_time_ms,
                client_ts=e.client_ts,
            )
        )
        accepted += 1
    await db.flush()
    return EventsBatchResponse(accepted=accepted, duplicates_ignored=dup)


async def submit_decision(
    db: AsyncSession,
    *,
    scenario_id: str,
    req: DecisionRequest,
) -> DecisionResponse:
    sc = await db.get(Scenario, scenario_id)
    if sc is None:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "scenario not found"})

    sess = await db.get(SessionModel, req.session_id)
    if sess is None:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "session not found"})

    opts_q = await db.execute(
        select(ScenarioOption)
        .where(ScenarioOption.scenario_id == scenario_id)
        .order_by(ScenarioOption.display_order)
    )
    opts = list(opts_q.scalars().all())
    if not opts:
        raise HTTPException(400, detail={"code": "SCENARIO_INVALID", "message": "scenario has no options"})

    chosen = next((o for o in opts if o.id == req.final_option_id), None)
    if chosen is None:
        raise HTTPException(
            400,
            detail={"code": "VALIDATION_ERROR", "message": "final_option_id does not belong to this scenario"},
        )

    existing_q = await db.execute(
        select(Decision).where(
            Decision.session_id == req.session_id,
            Decision.scenario_id == scenario_id,
        )
    )
    if existing_q.scalars().first() is not None:
        raise HTTPException(
            409,
            detail={"code": "CONFLICT", "message": "a decision already exists for this scenario and session"},
        )

    events_q = await db.execute(
        select(Event)
        .where(Event.session_id == req.session_id, Event.scenario_id == scenario_id)
        .order_by(Event.relative_time_ms)
    )
    events = [
        {
            "event_type": e.event_type,
            "option_id": e.option_id,
            "payload": e.payload or {},
            "relative_time_ms": e.relative_time_ms,
        }
        for e in events_q.scalars().all()
    ]

    label_by_id = {o.id: o.label for o in opts}
    raw = metrics_from_events(
        events,
        n_options=len(opts),
        option_label_by_id=label_by_id,
        time_pressure=sc.time_pressure,
        has_reveal=sc.has_reveal,
        information_availability=sc.information_availability,
    )

    decision = Decision(
        session_id=req.session_id,
        scenario_id=scenario_id,
        user_id=sess.user_id,
        first_option_viewed=raw.first_option_viewed,
        final_option_label=chosen.label,
        final_option_id=chosen.id,
        decision_latency_ms=raw.latency_ms,
        reversal_count=raw.n_reversals,
        unique_options_viewed=raw.n_unique_viewed,
        info_items_opened=raw.n_info_opened,
        self_confidence=req.self_confidence,
        reasoning_text=req.reasoning_text,
    )
    db.add(decision)
    await db.flush()

    computed = await compute_for_user(db, sess.user_id)
    kind = "initial" if computed["sample_count"] <= 1 else "pattern"
    profile = await persist_profile(db, sess.user_id, computed=computed, kind=kind)

    return DecisionResponse(
        decision_id=decision.id,
        derived=DecisionDerived(
            decision_latency_ms=raw.latency_ms,
            first_option_viewed=raw.first_option_viewed,
            unique_options_viewed=raw.n_unique_viewed,
            reversal_count=raw.n_reversals,
            info_items_opened=raw.n_info_opened,
        ),
        feature_vector=profile.features,
        profile_version=profile.version,
    )


__all__ = ["ingest_events", "submit_decision"]