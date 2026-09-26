"""The MIRROR predictor.

Pure computation. Input: a profile + a scenario + past scenarios. Output:
a fully materialized prediction. No DB, no LLM, no I/O.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from ..behavior import choice_model as cm
from ..behavior.constants import CHOICE_FEATURE_ORDER
from . import confidence as conf_mod


@dataclass
class PredictionComputation:
    predicted_first_label: str | None
    predicted_final_label: str
    predicted_style: str
    probability_distribution: dict[str, float]
    confidence: float
    confidence_parts: dict[str, float]
    confidence_bands: dict[str, list[str]]
    evidence: list[str]
    counterfactuals: str
    allowed_numbers: set[int] = field(default_factory=set)


def _option_dicts_from_model(options: list[dict]) -> list[dict]:
    return [
        {
            "label": str(o.get("label") or "?"),
            "attributes": o.get("attributes") or {},
        }
        for o in options
    ]


def _predict_first_action(
    features: dict[str, float | None],
    options: list[dict],
    final_label: str,
) -> str:
    """Stated heuristic; documented in docs/behavior-model.md.

    If the user shows a strong exploration or novelty signal, we predict they
    will look first at the most novel option. Otherwise we predict the first
    action matches the eventual final choice.
    """
    exploration = features.get("exploration")
    novelty = features.get("novelty_seeking")

    if (exploration is not None and exploration > 0.5) or (
        novelty is not None and novelty > 0.6
    ):
        best = max(
            options,
            key=lambda o: float((o.get("attributes") or {}).get("novelty", 0.0)),
        )
        return str(best["label"])
    return final_label


def _predict_style(features: dict[str, float | None]) -> str:
    exploration = features.get("exploration")
    speed = features.get("decision_speed")
    if exploration is not None and exploration > 0.6:
        return "explore_first"
    if speed is not None and speed > 0.7:
        return "commit_fast"
    return "balanced"


_STATEMENTS: dict[str, str] = {
    "decision_speed": "You tend to decide quickly relative to the number of options.",
    "exploration": "You usually inspect more than one option before deciding.",
    "risk_tolerance": "Your risk preference is measurable from past choices.",
    "evidence_seeking": "You tend to open additional information before deciding.",
    "reconsideration": "You sometimes revisit options before committing.",
    "consistency": "A single stable policy describes your past choices well.",
    "novelty_seeking": "You tend to weigh the less familiar option.",
    "uncertainty_tolerance": "You will accept options with more unknowns.",
    "adaptability": "You have responded to mid-scenario information changes.",
    "time_pressure_response": "Your behavior shifts under time pressure.",
}


def _build_bands(
    confidence: dict[str, dict],
) -> dict[str, list[str]]:
    high: list[str] = []
    medium: list[str] = []
    low: list[str] = []
    for name, c in confidence.items():
        level = (c or {}).get("level", "LOW")
        stmt = _STATEMENTS.get(name)
        if not stmt:
            continue
        if level == "HIGH":
            high.append(stmt)
        elif level == "MEDIUM":
            medium.append(stmt)
        else:
            low.append(
                f"Not enough observations yet to say anything about "
                f"{name.replace('_', ' ')}."
            )
    return {"high": high, "medium": medium, "low": low}


def _build_evidence(
    features: dict[str, float | None],
    confidence: dict[str, dict],
    n_decisions: int,
) -> list[str]:
    ev: list[str] = []
    ranked = sorted(
        confidence.items(),
        key=lambda kv: float((kv[1] or {}).get("score", 0.0)),
        reverse=True,
    )
    for name, c in ranked[:4]:
        score = float((c or {}).get("score", 0.0))
        if score < 0.3:
            continue
        stmt = _STATEMENTS.get(name)
        if not stmt:
            continue
        n = int((c or {}).get("n", 0))
        ev.append(f"{stmt} (observed across {n} scenario{'s' if n != 1 else ''}.)")
    if not ev:
        ev.append(
            f"Based on {n_decisions} observed decision"
            f"{'s' if n_decisions != 1 else ''} so far."
        )
    return ev


def _counterfactual(features: dict[str, float | None]) -> str:
    missing: list[str] = [
        name for name, v in features.items() if v is None
    ]
    if "adaptability" in missing:
        return (
            "This prediction has not been tested against scenarios where new "
            "information arrives mid-decision."
        )
    if "time_pressure_response" in missing:
        return (
            "A strict time limit may cause you to prioritize speed over "
            "comparison."
        )
    if "uncertainty_tolerance" in missing:
        return "More uncertainty in the scenario could flip this prediction."
    if "risk_tolerance" in missing:
        return "A scenario with a larger risk spread could change the prediction."
    return "Consistent behavior so far makes this prediction relatively stable."


def compute(
    *,
    profile_features: dict[str, float | None],
    profile_confidence: dict[str, dict],
    choice_weights: dict[str, float],
    n_decisions: int,
    target_scenario_attrs: dict[str, float],
    past_scenario_attrs: list[dict[str, float]],
    options: list[dict],
) -> PredictionComputation:
    option_dicts = _option_dicts_from_model(options)

    # --- final choice ---
    w = np.array(
        [float(choice_weights.get(name, 0.0)) for name in CHOICE_FEATURE_ORDER]
    )
    probs = cm.predict_options(w, option_dicts)
    prob_dict = {label: float(p) for label, p in probs}
    predicted_final, _ = max(probs, key=lambda x: x[1])

    # --- first action ---
    predicted_first = _predict_first_action(
        profile_features, option_dicts, predicted_final
    )

    # --- style ---
    style = _predict_style(profile_features)

    # --- confidence ---
    sim = conf_mod.similarity_term(target_scenario_attrs, past_scenario_attrs)
    dec = conf_mod.decisiveness_term([p for _, p in probs])
    sample = conf_mod.sample_support_term(n_decisions)
    conf_value, conf_parts = conf_mod.combine(
        scenario_similarity=sim,
        decisiveness=dec,
        sample_support=sample,
        n_decisions=n_decisions,
    )

    # --- bands ---
    bands = _build_bands(profile_confidence)

    # --- evidence ---
    evidence = _build_evidence(profile_features, profile_confidence, n_decisions)

    # --- counterfactual ---
    cf = _counterfactual(profile_features)

    # --- allowed numbers for narrative consistency check ---
    allowed: set[int] = {int(n_decisions), int(conf_value * 100)}
    for _, p in probs:
        allowed.add(int(p * 100))
    for stmt in evidence:
        for token in stmt.replace("(", " ").replace(")", " ").replace(".", " ").split():
            try:
                allowed.add(int(token))
            except ValueError:
                pass

    return PredictionComputation(
        predicted_first_label=predicted_first,
        predicted_final_label=predicted_final,
        predicted_style=style,
        probability_distribution=prob_dict,
        confidence=conf_value,
        confidence_parts=conf_parts,
        confidence_bands=bands,
        evidence=evidence,
        counterfactuals=cf,
        allowed_numbers=allowed,
    )


__all__ = ["PredictionComputation", "compute"]