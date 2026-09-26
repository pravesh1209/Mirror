"""Profile / fingerprint / stats routes.

These endpoints are strictly read-only. If no persisted profile exists yet,
they compute one transiently and return it — they never INSERT. Persistence
belongs to the decision-submit path (services/decisions.py), which is the
only place a new profile version is written.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..behavior.constants import CALIBRATION_MIN_RESOLVED, FEATURE_NAMES
from ..behavior.profile import compute_for_user, latest_profile
from ..db import get_session
from ..models import Decision, Prediction, PredictionResult, User
from ..schemas import (
    FeatureConfidence,
    FingerprintResponse,
    ProfileResponse,
    ProfileStats,
)

router = APIRouter(tags=["profile"])


def _empty_features() -> dict[str, float | None]:
    return {name: None for name in FEATURE_NAMES}


def _empty_confidence() -> dict[str, dict]:
    return {name: {"level": "LOW", "score": 0.0, "n": 0} for name in FEATURE_NAMES}


async def _resolve_profile_state(
    db: AsyncSession, user_id: str
) -> tuple[
    dict[str, float | None],
    dict[str, dict],
    int,          # sample_count
    int,          # version (0 when no persisted profile)
    list[str],    # pattern statements
    dict[str, float],  # choice weights
]:
    """Return the state to render, whether or not a persisted profile exists.

    When no profile is stored, we compute the feature vector transiently —
    it is honest and always reflects the current decision history.
    """
    prof = await latest_profile(db, user_id)
    if prof is not None:
        features = {name: (prof.features or {}).get(name) for name in FEATURE_NAMES}
        conf_in = prof.feature_confidence or {}
        conf = {
            name: conf_in.get(name) or {"level": "LOW", "score": 0.0, "n": 0}
            for name in FEATURE_NAMES
        }
        patterns = [
            p.get("statement", "")
            for p in (prof.known_patterns or [])
            if isinstance(p, dict)
        ]
        weights = {
            k: float(v) for k, v in (prof.choice_weights or {}).items()
        }
        return features, conf, int(prof.sample_count or 0), int(prof.version), patterns, weights

    computed = await compute_for_user(db, user_id)
    features = {name: computed["features"].get(name) for name in FEATURE_NAMES}
    conf = {
        name: (computed["feature_confidence"].get(name) or {"level": "LOW", "score": 0.0, "n": 0})
        for name in FEATURE_NAMES
    }
    weights = {
        k: float(v) for k, v in (computed.get("choice_weights") or {}).items()
    }
    return features, conf, int(computed["sample_count"]), 0, [], weights


@router.get("/profile/{user_id}/fingerprint", response_model=FingerprintResponse)
async def fingerprint(
    user_id: str,
    db: AsyncSession = Depends(get_session),
) -> FingerprintResponse:
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(
            404, detail={"code": "NOT_FOUND", "message": "user not found"}
        )

    features, conf_in, sample_count, version, patterns, _weights = await _resolve_profile_state(
        db, user_id
    )

    conf_out: dict[str, FeatureConfidence] = {}
    for name in FEATURE_NAMES:
        c = conf_in.get(name) or {"level": "LOW", "score": 0.0, "n": 0}
        conf_out[name] = FeatureConfidence(
            level=c.get("level", "LOW"),
            score=float(c.get("score", 0.0)),
            n=int(c.get("n", 0)),
        )

    insufficient = [name for name, v in features.items() if v is None]

    return FingerprintResponse(
        user_id=user_id,
        sample_count=sample_count,
        version=version,
        features=features,
        confidence=conf_out,
        patterns=patterns,
        insufficient=insufficient,
    )


async def _stats(db: AsyncSession, user_id: str) -> ProfileStats:
    obs_q = await db.execute(
        select(func.count(Decision.id)).where(Decision.user_id == user_id)
    )
    observations = int(obs_q.scalar_one() or 0)

    pred_q = await db.execute(
        select(func.count(Prediction.id)).where(Prediction.user_id == user_id)
    )
    predictions = int(pred_q.scalar_one() or 0)

    resolved_q = await db.execute(
        select(PredictionResult)
        .join(Prediction, Prediction.id == PredictionResult.prediction_id)
        .where(Prediction.user_id == user_id)
    )
    results = list(resolved_q.scalars().all())
    resolved = len(results)
    correct = sum(1 for r in results if r.choice_correct)
    top2 = sum(1 for r in results if r.top2_correct)

    choice_accuracy = (correct / resolved) if resolved else None
    top2_accuracy = (top2 / resolved) if resolved else None
    mean_brier = (sum(r.brier_score for r in results) / resolved) if resolved else None

    calibration_available = resolved >= CALIBRATION_MIN_RESOLVED
    note = (
        f"Prediction accuracy is reported after "
        f"{CALIBRATION_MIN_RESOLVED} resolved predictions, to avoid "
        f"over-interpreting very small samples. {resolved} so far."
    )

    return ProfileStats(
        observations=observations,
        predictions=predictions,
        resolved=resolved,
        correct=correct,
        choice_accuracy=choice_accuracy,
        top2_accuracy=top2_accuracy,
        mean_brier=mean_brier,
        calibration_available=calibration_available,
        calibration_note=note,
    )


@router.get("/profile/{user_id}/stats", response_model=ProfileStats)
async def stats(
    user_id: str,
    db: AsyncSession = Depends(get_session),
) -> ProfileStats:
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(
            404, detail={"code": "NOT_FOUND", "message": "user not found"}
        )
    return await _stats(db, user_id)


@router.get("/profile/{user_id}", response_model=ProfileResponse)
async def profile(
    user_id: str,
    db: AsyncSession = Depends(get_session),
) -> ProfileResponse:
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(
            404, detail={"code": "NOT_FOUND", "message": "user not found"}
        )

    features, _conf, sample_count, version, _patterns, weights = await _resolve_profile_state(
        db, user_id
    )
    st = await _stats(db, user_id)

    return ProfileResponse(
        user_id=user_id,
        version=version,
        sample_count=sample_count,
        features=features,
        choice_weights=weights,
        stats=st,
    )


@router.delete("/profile/{user_id}", status_code=204)
async def delete_profile(
    user_id: str,
    db: AsyncSession = Depends(get_session),
) -> None:
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(
            404, detail={"code": "NOT_FOUND", "message": "user not found"}
        )
    await db.delete(user)
    await db.flush()