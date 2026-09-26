"""Prediction accuracy metrics.

Everything here is deterministic. The numbers shown to the user come from
these functions, never from an LLM.
"""
from __future__ import annotations

import math
from typing import Mapping


def brier_score(prob_dist: Mapping[str, float], chosen_label: str) -> float:
    """Multiclass Brier score for a single prediction. Lower is better (0..2)."""
    total = 0.0
    for label, p in prob_dist.items():
        target = 1.0 if label == chosen_label else 0.0
        total += (float(p) - target) ** 2
    return float(total)


def choice_correct(prob_dist: Mapping[str, float], chosen_label: str) -> bool:
    if not prob_dist:
        return False
    return max(prob_dist.items(), key=lambda kv: kv[1])[0] == chosen_label


def top2_correct(prob_dist: Mapping[str, float], chosen_label: str) -> bool:
    if not prob_dist:
        return False
    ranked = sorted(prob_dist.items(), key=lambda kv: kv[1], reverse=True)[:2]
    return chosen_label in {r[0] for r in ranked}


def feature_similarity(
    predicted: Mapping[str, float | None],
    actual: Mapping[str, float | None],
) -> float:
    """1 - normalized euclidean distance over the axes both have values for."""
    keys = [k for k in predicted if predicted.get(k) is not None and actual.get(k) is not None]
    if not keys:
        return 0.0
    s = 0.0
    for k in keys:
        d = float(predicted[k]) - float(actual[k])
        s += d * d
    dist = math.sqrt(s) / math.sqrt(len(keys))
    return float(max(0.0, min(1.0, 1.0 - dist)))


def predicted_style(
    unique_options_viewed: int,
    n_options: int,
    latency_ms: int,
    first_touch_ms: int | None,
) -> str:
    """Classify a scenario into explore / commit_fast / balanced."""
    if n_options <= 1:
        return "balanced"
    if unique_options_viewed >= 2:
        return "explore_first"
    if first_touch_ms is not None and latency_ms - first_touch_ms <= 3000:
        return "commit_fast"
    return "balanced"


__all__ = [
    "brier_score",
    "choice_correct",
    "top2_correct",
    "feature_similarity",
    "predicted_style",
]