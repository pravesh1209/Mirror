"""Prediction orchestration: DB -> engine -> persistence."""
from __future__ import annotations

import logging

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..behavior.constants import MIN_SAMPLES_TO_PREDICT
from ..behavior.profile import compute_for_user, latest_profile, persist_profile
from ..models import Decision, Prediction, PredictionResult, Scenario, ScenarioOption
from ..prediction import counterfactual as cf
from ..prediction.compare import build_compare, _actual_style
from ..prediction.engine import compute
from ..prediction.explain import build_narrative
from ..schemas import (
    CompareMetrics,
    CompareRow,
    ErrorAnalysis,
    PredictionRequest,
    PredictionResponse,
    PredictedOption,
    ResolveResponse,
    WhatIfResponse,
)
from .reflection import reflect_on_miss

log = logging.getLogger("mirror.services.predictions")


async def _load_option_bundle(
    db: AsyncSession, scenario_id: str
) -> list[ScenarioOption]:
    q = await db.execute(
        select(ScenarioOption)
        .where(ScenarioOption.scenario_id == scenario_id)
        .order_by(ScenarioOption.display_order)
    )
    return list(q.scalars().all())


def _option_dicts(opts: list[ScenarioOption]) -> list[dict]:
    return [
        {
            "label": o.label,
            "id": o.id,
            "title": o.title,
            "attributes": {
                "risk": o.risk,
                "time_cost": o.time_cost,
                "money_cost": o.money_cost,
                "novelty": o.novelty,
                "uncertainty": o.uncertainty,
                "info_availability": o.info_availability,
                "reward": o.reward,
            },
        }
        for o in opts
    ]


def _scenario_attrs(sc: Scenario) -> dict[str, float]:
    return {
        "difficulty": sc.difficulty,
        "risk": sc.risk,
        "uncertainty": sc.uncertainty,
        "time_pressure": sc.time_pressure,
        "novelty": sc.novelty,
        "reward": sc.reward,
        "information_availability": sc.information_availability,
    }


async def _past_scenario_attrs(
    db: AsyncSession, user_id: str, exclude_scenario_id: str
) -> list[dict[str, float]]:
    q = await db.execute(select(Decision).where(Decision.user_id == user_id))
    out: list[dict[str, float]] = []
    for d in q.scalars().all():
        if d.scenario_id == exclude_scenario_id:
            continue
        sc = await db.get(Scenario, d.scenario_id)
        if sc is not None:
            out.append(_scenario_attrs(sc))
    return out


def _to_response(pred: Prediction, options: list[ScenarioOption]) -> PredictionResponse:
    label_to_option = {o.label: o for o in options}
    dist = pred.prob_distribution or {}

    final_opt = label_to_option.get(pred.predicted_final_label)
    if final_opt is None:
        raise HTTPException(
            500,
            detail={"code": "INTERNAL", "message": "stored prediction references missing option"},
        )

    first: PredictedOption | None = None
    if pred.predicted_first_label:
        first_opt = label_to_option.get(pred.predicted_first_label)
        if first_opt is not None:
            first = PredictedOption(
                label=first_opt.label,
                option_id=first_opt.id,
                probability=float(dist.get(first_opt.label, 0.0)),
            )

    return PredictionResponse(
        prediction_id=pred.id,
        profile_version=pred.profile_version,
        predicted_first_option=first,
        predicted_final_option=PredictedOption(
            label=final_opt.label,
            option_id=final_opt.id,
            probability=float(dist.get(final_opt.label, 0.0)),
        ),
        probability_distribution=dist,
        predicted_style=pred.predicted_style,
        confidence=float(pred.confidence),
        confidence_parts={k: float(v) for k, v in (pred.confidence_parts or {}).items()},
        confidence_bands=pred.confidence_bands or {"high": [], "medium": [], "low": []},
        what_could_change_it=pred.counterfactuals,
        evidence=[str(e) for e in (pred.evidence or [])],
        narrative=pred.narrative,
        narrative_source=pred.narrative_source,
    )


async def create_prediction(
    db: AsyncSession, req: PredictionRequest
) -> PredictionResponse:
    prof = await latest_profile(db, req.user_id)
    if prof is None or (prof.sample_count or 0) < MIN_SAMPLES_TO_PREDICT:
        raise HTTPException(
            409,
            detail={
                "code": "NO_PROFILE",
                "message": "Not enough observations yet to make a prediction.",
            },
        )

    sc = await db.get(Scenario, req.scenario_id)
    if sc is None:
        raise HTTPException(
            404, detail={"code": "NOT_FOUND", "message": "scenario not found"}
        )
    if sc.user_id is not None and sc.user_id != req.user_id:
        raise HTTPException(
            403,
            detail={"code": "FORBIDDEN", "message": "scenario belongs to another user"},
        )

    opts = await _load_option_bundle(db, req.scenario_id)
    if not opts:
        raise HTTPException(
            400,
            detail={"code": "SCENARIO_INVALID", "message": "scenario has no options"},
        )

    past = await _past_scenario_attrs(db, req.user_id, req.scenario_id)

    comp = compute(
        profile_features=prof.features or {},
        profile_confidence=prof.feature_confidence or {},
        choice_weights=prof.choice_weights or {},
        n_decisions=prof.sample_count or 0,
        target_scenario_attrs=_scenario_attrs(sc),
        past_scenario_attrs=past,
        options=_option_dicts(opts),
    )

    label_to_option = {o.label: o for o in opts}
    final_opt = label_to_option[comp.predicted_final_label]

    narrative, source = await build_narrative(
        comp, final_label=final_opt.label, final_title=final_opt.title
    )

    pred = Prediction(
        user_id=req.user_id,
        scenario_id=req.scenario_id,
        profile_version=prof.version,
        predicted_first_label=comp.predicted_first_label,
        predicted_final_label=comp.predicted_final_label,
        predicted_style=comp.predicted_style,
        prob_distribution=comp.probability_distribution,
        confidence=comp.confidence,
        confidence_parts=comp.confidence_parts,
        confidence_bands=comp.confidence_bands,
        evidence=comp.evidence,
        counterfactuals=comp.counterfactuals,
        narrative=narrative,
        narrative_source=source,
    )
    db.add(pred)
    await db.flush()
    return _to_response(pred, opts)


async def get_prediction(db: AsyncSession, prediction_id: str) -> PredictionResponse:
    pred = await db.get(Prediction, prediction_id)
    if pred is None:
        raise HTTPException(
            404, detail={"code": "NOT_FOUND", "message": "prediction not found"}
        )
    opts = await _load_option_bundle(db, pred.scenario_id)
    return _to_response(pred, opts)


async def resolve_prediction(
    db: AsyncSession, *, prediction_id: str, decision_id: str
) -> ResolveResponse:
    pred = await db.get(Prediction, prediction_id)
    if pred is None:
        raise HTTPException(
            404, detail={"code": "NOT_FOUND", "message": "prediction not found"}
        )
    dec = await db.get(Decision, decision_id)
    if dec is None:
        raise HTTPException(
            404, detail={"code": "NOT_FOUND", "message": "decision not found"}
        )
    if pred.scenario_id != dec.scenario_id:
        raise HTTPException(
            400,
            detail={
                "code": "VALIDATION_ERROR",
                "message": "prediction and decision are for different scenarios",
            },
        )
    existing_q = await db.execute(
        select(PredictionResult).where(PredictionResult.prediction_id == prediction_id)
    )
    if existing_q.scalars().first() is not None:
        raise HTTPException(
            409,
            detail={"code": "CONFLICT", "message": "prediction already resolved"},
        )

    sc = await db.get(Scenario, pred.scenario_id)
    opts = await _load_option_bundle(db, pred.scenario_id)
    label_to_option = {o.label: o for o in opts}
    actual_final = label_to_option.get(dec.final_option_label)
    if actual_final is None:
        raise HTTPException(
            400,
            detail={"code": "VALIDATION_ERROR", "message": "decision references unknown option"},
        )

    actual_style = _actual_style(
        unique_options_viewed=dec.unique_options_viewed,
        n_options=len(opts),
        latency_ms=dec.decision_latency_ms,
        first_touch_ms=None,
    )

    computed = await compute_for_user(db, pred.user_id)

    payload = build_compare(
        predicted_first_label=pred.predicted_first_label,
        predicted_final_label=pred.predicted_final_label,
        predicted_style_label=pred.predicted_style,
        probability_distribution=pred.prob_distribution or {},
        actual_first_label=dec.first_option_viewed,
        actual_final_label=dec.final_option_label,
        actual_style_label=actual_style,
        n_options=len(opts),
        unique_options_viewed=dec.unique_options_viewed,
        latency_ms=dec.decision_latency_ms,
        first_touch_ms=None,
        predicted_profile=computed["features"],
        actual_profile=computed["features"],
    )

    error_analysis: dict | None = None
    if payload.miss:
        error_analysis = await reflect_on_miss(
            predicted_label=pred.predicted_final_label,
            actual_label=dec.final_option_label,
            features=computed["features"],
            confidence_parts=pred.confidence_parts or {},
        )

    result = PredictionResult(
        prediction_id=prediction_id,
        decision_id=decision_id,
        choice_correct=payload.metrics["choice_correct"],
        top2_correct=payload.metrics["top2_correct"],
        first_action_correct=(
            pred.predicted_first_label == dec.first_option_viewed
            if dec.first_option_viewed
            else None
        ),
        style_correct=pred.predicted_style == actual_style,
        brier_score=payload.metrics["brier_score"],
        feature_similarity=payload.metrics["feature_similarity"],
        error_analysis=error_analysis,
    )
    db.add(result)

    kind = "correction" if payload.miss else "pattern"
    await persist_profile(
        db,
        pred.user_id,
        computed=computed,
        trigger_prediction_id=prediction_id,
        kind=kind,
        failed_assumption=(error_analysis or {}).get("failed_assumption"),
        new_evidence=(error_analysis or {}).get("new_evidence"),
    )
    await db.flush()

    return ResolveResponse(
        prediction_id=prediction_id,
        rows=[CompareRow(**r) for r in payload.rows],
        metrics=CompareMetrics(**payload.metrics),
        error_analysis=ErrorAnalysis(**error_analysis) if error_analysis else None,
    )


async def whatif_prediction(
    db: AsyncSession,
    *,
    prediction_id: str,
    overrides: dict[str, float],
) -> WhatIfResponse:
    pred = await db.get(Prediction, prediction_id)
    if pred is None:
        raise HTTPException(
            404, detail={"code": "NOT_FOUND", "message": "prediction not found"}
        )
    sc = await db.get(Scenario, pred.scenario_id)
    if sc is None:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "scenario not found"})
    opts = await _load_option_bundle(db, pred.scenario_id)

    prof = await latest_profile(db, pred.user_id)
    if prof is None:
        raise HTTPException(
            409, detail={"code": "NO_PROFILE", "message": "no profile available"}
        )

    option_dicts = _option_dicts(opts)
    new_sc, new_opts = cf.apply_overrides(
        scenario_attrs=_scenario_attrs(sc),
        option_dicts=option_dicts,
        overrides=overrides,
    )

    past = await _past_scenario_attrs(db, pred.user_id, pred.scenario_id)

    comp = compute(
        profile_features=prof.features or {},
        profile_confidence=prof.feature_confidence or {},
        choice_weights=prof.choice_weights or {},
        n_decisions=prof.sample_count or 0,
        target_scenario_attrs=new_sc,
        past_scenario_attrs=past,
        options=new_opts,
    )

    return WhatIfResponse(
        previous_final=pred.predicted_final_label,
        new_final=comp.predicted_final_label,
        reason=cf.reason_text(overrides),
        delta_confidence=round(float(comp.confidence) - float(pred.confidence), 4),
    )


__all__ = [
    "create_prediction",
    "get_prediction",
    "resolve_prediction",
    "whatif_prediction",
]