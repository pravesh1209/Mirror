"""Profile orchestrator.

Loads a user's decisions, events, scenarios and options, computes the full
behavior model, and writes a new versioned BehaviorProfile row.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import (
    BehaviorFeature,
    BehaviorProfile,
    Decision,
    Event,
    ModelUpdate,
    Scenario,
    ScenarioOption,
    User,
)
from . import choice_model as cm
from . import features as feat
from . import similarity as sim
from .events import RawMetrics, apply_choice_exposures, metrics_from_events


async def _load_scenario_bundle(
    session: AsyncSession, scenario_id: str
) -> tuple[Scenario | None, list[ScenarioOption]]:
    sc = await session.get(Scenario, scenario_id)
    if sc is None:
        return None, []
    opts_q = await session.execute(
        select(ScenarioOption)
        .where(ScenarioOption.scenario_id == scenario_id)
        .order_by(ScenarioOption.display_order)
    )
    return sc, list(opts_q.scalars().all())


async def _events_for(session: AsyncSession, scenario_id: str, session_id: str) -> list[dict]:
    q = await session.execute(
        select(Event).where(
            Event.scenario_id == scenario_id,
            Event.session_id == session_id,
        )
    )
    out: list[dict] = []
    for e in q.scalars().all():
        out.append(
            {
                "event_type": e.event_type,
                "option_id": e.option_id,
                "payload": e.payload or {},
                "relative_time_ms": e.relative_time_ms,
            }
        )
    return out


async def compute_for_user(session: AsyncSession, user_id: str) -> dict[str, Any]:
    """Return a fully computed profile dictionary for the given user.

    Does not persist.
    """
    decisions_q = await session.execute(
        select(Decision).where(Decision.user_id == user_id).order_by(Decision.submitted_at)
    )
    decisions = list(decisions_q.scalars().all())

    per_scenario: list[RawMetrics] = []
    dataset = cm.ChoiceDataset(scenarios=[], chosen_indices=[], option_labels=[])
    scenario_attrs_history: list[dict] = []

    for d in decisions:
        sc, opts = await _load_scenario_bundle(session, d.scenario_id)
        if sc is None or not opts:
            continue
        option_label_by_id = {o.id: o.label for o in opts}

        raw = metrics_from_events(
            await _events_for(session, d.scenario_id, d.session_id),
            n_options=len(opts),
            option_label_by_id=option_label_by_id,
            time_pressure=sc.time_pressure,
            has_reveal=sc.has_reveal,
            information_availability=sc.information_availability,
        )
        # overlay the DB decision row for authoritative fields
        raw.final_option_label = d.final_option_label
        raw.n_reversals = max(raw.n_reversals, d.reversal_count)
        raw.n_unique_viewed = max(raw.n_unique_viewed, d.unique_options_viewed)
        raw.n_info_opened = max(raw.n_info_opened, d.info_items_opened)
        if d.decision_latency_ms:
            raw.latency_ms = d.decision_latency_ms
            if raw.n_options > 0:
                raw.speed_raw = raw.latency_ms / float(raw.n_options)
        if d.first_option_viewed:
            raw.first_option_viewed = d.first_option_viewed

        option_dicts = [
            {
                "label": o.label,
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
        apply_choice_exposures(raw, chosen_label=d.final_option_label, options=option_dicts)
        per_scenario.append(raw)

        # build choice dataset row
        chosen_idx = next(
            (i for i, o in enumerate(opts) if o.label == d.final_option_label),
            None,
        )
        if chosen_idx is not None:
            import numpy as np
            X = np.stack(
                [cm.option_vector(o["attributes"]) for o in option_dicts]
            )
            dataset.scenarios.append(X)
            dataset.chosen_indices.append(chosen_idx)
            dataset.option_labels.append([o.label for o in opts])

        scenario_attrs_history.append(
            {
                "difficulty": sc.difficulty,
                "risk": sc.risk,
                "uncertainty": sc.uncertainty,
                "time_pressure": sc.time_pressure,
                "novelty": sc.novelty,
                "reward": sc.reward,
                "information_availability": sc.information_availability,
            }
        )

    # --- fit choice model ---
    weights = cm.fit(dataset) if dataset.scenarios else None
    consistency = cm.consistency_score(weights, dataset) if weights is not None else None

    # --- compute features ---
    fr = feat.compute_features(per_scenario, consistency=consistency)
    conf = feat.confidence_map(fr)

    # --- build narrative lists (patterns / uncertainties) ---
    patterns: list[dict] = []
    uncertainties: list[dict] = []
    for name in feat.FEATURE_NAMES:
        fv = fr.features.get(name)
        c = conf.get(name) or {}
        if fv is None or (c.get("n") or 0) < 3:
            uncertainties.append(
                {
                    "axis": name,
                    "reason": "Not enough observations yet.",
                    "n": int(c.get("n") or 0),
                }
            )
            continue
        if fv >= 0.65:
            patterns.append(
                {
                    "axis": name,
                    "statement": _pattern_statement(name, "high"),
                    "support_n": int(c.get("n") or 0),
                }
            )
        elif fv <= 0.35:
            patterns.append(
                {
                    "axis": name,
                    "statement": _pattern_statement(name, "low"),
                    "support_n": int(c.get("n") or 0),
                }
            )

    sample_count = len(per_scenario)
    return {
        "sample_count": sample_count,
        "features": fr.features,
        "feature_confidence": conf,
        "choice_weights": cm.weights_as_dict(weights) if weights is not None else {},
        "known_patterns": patterns,
        "uncertainties": uncertainties,
        "scenario_attrs_history": scenario_attrs_history,
        "per_scenario": per_scenario,
        "dataset": dataset,
        "weights": weights,
    }


async def persist_profile(
    session: AsyncSession,
    user_id: str,
    *,
    computed: dict[str, Any],
    trigger_prediction_id: str | None = None,
    kind: str = "initial",
    narrative: str = "",
    failed_assumption: str | None = None,
    new_evidence: str | None = None,
) -> BehaviorProfile:
    """Write a new profile version and record a ModelUpdate row."""
    last_q = await session.execute(
        select(BehaviorProfile)
        .where(BehaviorProfile.user_id == user_id)
        .order_by(BehaviorProfile.version.desc())
        .limit(1)
    )
    last = last_q.scalars().first()
    prev_version = last.version if last else 0
    deltas: dict[str, dict[str, float]] = {}
    if last:
        for k, v in computed["features"].items():
            old = (last.features or {}).get(k)
            if v is not None and old is not None and abs(v - old) > 1e-6:
                deltas[k] = {"before": float(old), "after": float(v)}

    profile = BehaviorProfile(
        user_id=user_id,
        version=prev_version + 1,
        sample_count=computed["sample_count"],
        features=computed["features"],
        feature_confidence=computed["feature_confidence"],
        choice_weights=computed["choice_weights"],
        known_patterns=computed["known_patterns"],
        uncertainties=computed["uncertainties"],
        blind_spots=[],
    )
    session.add(profile)
    try:
        await session.flush()
    except IntegrityError:
        # A concurrent request created the same version. Fall back to the
        # version that just won the race; do not raise.
        await session.rollback()
        existing = await latest_profile(session, user_id)
        if existing is None:
            raise
        return existing

    update = ModelUpdate(
        user_id=user_id,
        from_version=prev_version,
        to_version=profile.version,
        trigger_prediction_id=trigger_prediction_id,
        kind=kind,
        feature_deltas=deltas,
        failed_assumption=failed_assumption,
        new_evidence=new_evidence,
        narrative=narrative or _default_narrative(kind, computed, deltas),
    )
    session.add(update)
    return profile


def _pattern_statement(axis: str, direction: str) -> str:
    table = {
        ("decision_speed", "high"): "Decided quickly relative to the option count.",
        ("decision_speed", "low"): "Took time before committing to a choice.",
        ("exploration", "high"): "Inspected multiple options before deciding.",
        ("exploration", "low"): "Tended to decide after limited inspection.",
        ("evidence_seeking", "high"): "Opened additional information before deciding.",
        ("evidence_seeking", "low"): "Decided without opening much extra information.",
        ("reconsideration", "high"): "Changed or revisited options frequently.",
        ("reconsideration", "low"): "Rarely reversed or revisited a choice.",
        ("risk_tolerance", "high"): "Tended toward higher-risk options when a spread existed.",
        ("risk_tolerance", "low"): "Tended toward lower-risk options when a spread existed.",
        ("novelty_seeking", "high"): "Tended toward the less familiar option.",
        ("novelty_seeking", "low"): "Tended toward the more familiar option.",
        ("uncertainty_tolerance", "high"): "Accepted options with less information.",
        ("uncertainty_tolerance", "low"): "Preferred options with more information.",
        ("adaptability", "high"): "Changed course when new information arrived.",
        ("adaptability", "low"): "Kept the same course after new information arrived.",
        ("consistency", "high"): "Choices were well described by a single stable policy.",
        ("consistency", "low"): "Choices were not well described by any single policy.",
    }
    return table.get((axis, direction), f"Observed pattern on axis '{axis}'.")


def _default_narrative(kind: str, computed: dict, deltas: dict) -> str:
    n = computed["sample_count"]
    if kind == "initial":
        return f"Initial model created from {n} completed scenario{'' if n == 1 else 's'}."
    if kind == "correction":
        return f"Model updated after a prediction miss ({n} completed scenario{'' if n == 1 else 's'} total)."
    if deltas:
        changed = ", ".join(sorted(deltas.keys()))
        return f"Model updated on {n} completed scenario{'' if n == 1 else 's'}. Changed axes: {changed}."
    return f"Model updated on {n} completed scenario{'' if n == 1 else 's'} (no significant axis change)."


async def latest_profile(session: AsyncSession, user_id: str) -> BehaviorProfile | None:
    q = await session.execute(
        select(BehaviorProfile)
        .where(BehaviorProfile.user_id == user_id)
        .order_by(BehaviorProfile.version.desc())
        .limit(1)
    )
    return q.scalars().first()


async def record_feature_row(
    session: AsyncSession,
    *,
    user_id: str,
    session_id: str,
    scenario_id: str,
    feature_vector: dict,
    raw_metrics: dict,
) -> BehaviorFeature:
    row = BehaviorFeature(
        user_id=user_id,
        session_id=session_id,
        scenario_id=scenario_id,
        feature_vector=feature_vector,
        raw_metrics=raw_metrics,
    )
    session.add(row)
    return row


__all__ = [
    "compute_for_user",
    "persist_profile",
    "latest_profile",
    "record_feature_row",
]