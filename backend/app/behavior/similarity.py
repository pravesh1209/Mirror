"""Scenario-to-scenario distance in attribute space."""
from __future__ import annotations

import math
from typing import Mapping, Sequence

from .constants import SCENARIO_AXES


def _vec(attrs: Mapping[str, float]) -> list[float]:
    return [float(attrs.get(a, 0.5)) for a in SCENARIO_AXES]


def scenario_distance(a: Mapping[str, float], b: Mapping[str, float]) -> float:
    """Euclidean distance in [0,1]^d, normalized by sqrt(d) so range is [0,1]."""
    va, vb = _vec(a), _vec(b)
    s = sum((x - y) ** 2 for x, y in zip(va, vb))
    d = len(SCENARIO_AXES)
    return math.sqrt(s) / math.sqrt(d) if d else 0.0


def mean_knn_distance(
    target: Mapping[str, float],
    history: Sequence[Mapping[str, float]],
    k: int = 3,
) -> float | None:
    """Mean distance to the k nearest historical scenarios.

    Returns None when there is no history.
    """
    if not history:
        return None
    dists = sorted(scenario_distance(target, h) for h in history)
    take = dists[: max(1, min(k, len(dists)))]
    return sum(take) / len(take)


__all__ = ["scenario_distance", "mean_knn_distance"]