"""Blind spot routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..behavior.constants import FEATURE_NAMES
from ..behavior.profile import compute_for_user, latest_profile
from ..blindspots import active_learning
from ..blindspots.detector import (
    axis_statement,
    detect_blind_spots,
    persist_blind_spots,
)
from ..db import get_session
from ..models import User
from ..models import Session as SessionModel
from ..schemas import (
    BlindSpotAxis,
    BlindSpotTestRequest,
    BlindSpotTestResponse,
    BlindSpotsAnalyzeRequest,
    BlindSpotsResponse,
)
from ..services import scenarios as sc_svc
from ..services.sessions import create_session

router = APIRouter(tags=["blind-spots"])


async def _confidence_for(db: AsyncSession, user_id: str) -> dict[str, dict]:
    """Return the current per-axis confidence map, computing transiently if needed."""
    prof = await latest_profile(db, user_id)
    if prof is not None and prof.feature_confidence:
        return prof.feature_confidence
    computed = await compute_for_user(db, user_id)
    return computed["feature_confidence"]


async def _run_detect(db: AsyncSession, user_id: str) -> list[dict]:
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(
            404, detail={"code": "NOT_FOUND", "message": "user not found"}
        )
    conf = await _confidence_for(db, user_id)
    detections = await detect_blind_spots(db, user_id=user_id, profile_confidence=conf)
    await persist_blind_spots(db, user_id=user_id, detections=detections)
    return detections


@router.post("/blind-spots/analyze", response_model=BlindSpotsResponse)
async def analyze(
    payload: BlindSpotsAnalyzeRequest,
    db: AsyncSession = Depends(get_session),
) -> BlindSpotsResponse:
    user = await db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(
            404, detail={"code": "NOT_FOUND", "message": "user not found"}
        )

    conf = await _confidence_for(db, payload.user_id)
    detections = await detect_blind_spots(
        db, user_id=payload.user_id, profile_confidence=conf
    )
    await persist_blind_spots(db, user_id=payload.user_id, detections=detections)

    detected_axes = {d["axis"] for d in detections}

    known: list[BlindSpotAxis] = []
    unknown: list[BlindSpotAxis] = []

    for axis in FEATURE_NAMES:
        if axis in detected_axes:
            continue
        c = conf.get(axis) or {}
        known.append(
            BlindSpotAxis(
                axis=axis,
                statement=axis_statement(axis),
                n=int(c.get("n", 0)),
                kind=None,
                severity=None,
            )
        )

    for d in detections:
        unknown.append(
            BlindSpotAxis(
                axis=d["axis"],
                statement=d.get("statement") or axis_statement(d["axis"]),
                n=d["evidence_count"],
                kind=d["kind"],
                severity=d["severity"],
            )
        )

    return BlindSpotsResponse(known=known, unknown=unknown)


@router.post("/blind-spots/test", response_model=BlindSpotTestResponse)
async def test_axis(
    payload: BlindSpotTestRequest,
    db: AsyncSession = Depends(get_session),
) -> BlindSpotTestResponse:
    user = await db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(
            404, detail={"code": "NOT_FOUND", "message": "user not found"}
        )

    s_q = await db.execute(
        select(SessionModel)
        .where(SessionModel.user_id == payload.user_id)
        .order_by(SessionModel.started_at.desc())
        .limit(1)
    )
    sess = s_q.scalars().first()
    if sess is None:
        _, sess = await create_session(db, display_name=None, mode="live")

    detections = await _run_detect(db, payload.user_id)
    evidence_count = 0
    for d in detections:
        if d["axis"] == payload.axis:
            evidence_count = int(d["evidence_count"])
            break

    best = active_learning.pick_best_scenario(
        axis=payload.axis,
        evidence_count=evidence_count,
    )

    from ..ai.schemas import GeneratedScenario

    gen = GeneratedScenario.model_validate(best)
    sc = await sc_svc._persist_generated(db, sess=sess, gen=gen, source="seed")
    sc_out = await sc_svc.get_scenario_out(db, sc.id)
    return BlindSpotTestResponse(scenario=sc_out)