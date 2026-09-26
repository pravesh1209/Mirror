"""Active learning: pick the next scenario that most reduces uncertainty.

Simple scoring over a candidate set:
  information_value = axis_spread * axis_gap * novelty_bonus

  axis_spread   how much the target axis varies across the options (0-1)
  axis_gap      how under-observed the axis is (1 - n / low_n_threshold)
  novelty_bonus small bonus if the scenario is one we have not shown

This is deliberately not a learned acquisition function. It is stated,
auditable, and good enough at n=8.
"""
from __future__ import annotations

from typing import Iterable, Mapping

from ..simulation.scenarios_core import SCENARIOS
from .detector import LOW_N_THRESHOLD, preferred_scenarios_for

_AXIS_TO_OPTION_ATTR: dict[str, str] = {
    "risk_tolerance": "risk",
    "novelty_seeking": "novelty",
    "uncertainty_tolerance": "uncertainty",
    "evidence_seeking": "info_availability",
    "adaptability": "uncertainty",
    "time_pressure_response": "time_cost",
    "reconsideration": "uncertainty",
    "exploration": "novelty",
    "consistency": "reward",
    "decision_speed": "time_cost",
}


def _spread(values: list[float]) -> float:
    if not values:
        return 0.0
    return max(values) - min(values)


def score_scenario(
    scenario: Mapping,
    *,
    axis: str,
    evidence_count: int,
    seen_titles: set[str],
) -> float:
    opt_attr = _AXIS_TO_OPTION_ATTR.get(axis, "reward")
    values = [
        float((o.get("attributes") or {}).get(opt_attr, 0.5))
        for o in scenario.get("options", [])
    ]
    spread = _spread(values)

    # scenario-attribute exposure on the axis also counts
    scene_spread = float(scenario.get(axis, 0.0) or 0.0)

    gap = max(0.0, 1.0 - (evidence_count / LOW_N_THRESHOLD))
    novelty_bonus = 0.15 if scenario.get("title") not in seen_titles else 0.0
    preferred_bonus = 0.10 if scenario.get("title") in preferred_scenarios_for(axis) else 0.0

    return round(
        (0.6 * spread + 0.4 * scene_spread) * gap + novelty_bonus + preferred_bonus,
        4,
    )


def pick_best_scenario(
    *,
    axis: str,
    evidence_count: int,
    seen_titles: Iterable[str] | None = None,
    candidates: list[dict] | None = None,
) -> dict:
    seen = set(seen_titles or [])
    pool = candidates if candidates is not None else list(SCENARIOS)
    if not pool:
        pool = list(SCENARIOS)

    scored = [
        (score_scenario(s, axis=axis, evidence_count=evidence_count, seen_titles=seen), s)
        for s in pool
    ]
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]


__all__ = ["score_scenario", "pick_best_scenario"]