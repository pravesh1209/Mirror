"""Selection logic over the deterministic scenario bank."""
from __future__ import annotations

import random
from typing import Any

from .scenarios_core import SCENARIOS


def all_scenarios() -> list[dict[str, Any]]:
    """Return a deep copy so callers can mutate safely."""
    import copy
    return copy.deepcopy(SCENARIOS)


def by_domain(domain: str | None) -> list[dict[str, Any]]:
    if not domain:
        return all_scenarios()
    filtered = [s for s in SCENARIOS if s["domain"] == domain]
    return filtered or all_scenarios()


def pick_for_calibration(used_titles: set[str]) -> dict[str, Any] | None:
    """Return the next unused bank scenario, or None if exhausted."""
    pool = [s for s in SCENARIOS if s["title"] not in used_titles]
    if not pool:
        return None
    import copy
    return copy.deepcopy(pool[0])


def pick_targeting_axis(axis: str) -> dict[str, Any]:
    """Return the bank scenario that best isolates the requested axis.

    The heuristics below are stated, not learned. They are enough for the
    hackathon demo; a learned version would score by information gain.
    """
    import copy

    # Preference order per axis. Each list is a domain/title hint.
    preferred = {
        "adaptability": ["An unplanned course opportunity", "An unexpected internal move"],
        "uncertainty_tolerance": ["An unfamiliar investment", "Two job offers, very different shapes"],
        "risk_tolerance": ["Two job offers, very different shapes", "Where the extra $500 goes"],
        "novelty_seeking": ["An unplanned course opportunity", "An unfamiliar investment"],
        "time_pressure_response": ["Getting across town", "A day with too many open threads"],
        "consistency": ["How to study for a hard exam", "Where the extra $500 goes"],
    }

    for hint in preferred.get(axis, []):
        for s in SCENARIOS:
            if hint.lower() in s["title"].lower():
                return copy.deepcopy(s)

    return copy.deepcopy(random.choice(SCENARIOS))


def pick_blind_spot_axis(axis: str) -> dict[str, Any]:
    return pick_targeting_axis(axis)


__all__ = [
    "all_scenarios",
    "by_domain",
    "pick_for_calibration",
    "pick_targeting_axis",
    "pick_blind_spot_axis",
]