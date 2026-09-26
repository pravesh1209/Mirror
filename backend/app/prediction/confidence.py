"""Confidence formula and bands for MIRROR predictions.

confidence = 0.40 * scenario_similarity
           + 0.35 * decisiveness
           + 0.25 * sample_support

Cold-start caps:
  n_decisions <  5  ->  cap at CONF_CAP_UNDER_5
  n_decisions < 10  ->  cap at CONF_CAP_UNDER_10
"""
from __future__ import annotations

import math

from ..behavior.constants import (
    CONF_BAND_HIGH,
    CONF_BAND_MEDIUM,
    CONF_CAP_UNDER_10,
    CONF_CAP_UNDER_5,
    CONF_SIM_D_MAX,
    CONF_WEIGHT_DECISIVE,
    CONF_WEIGHT_SAMPLE,
    CONF_WEIGHT_SIM,
)
from ..behavior.similarity import mean_knn_distance


def similarity_term(
    target_attrs: dict[str, float],
    past_attrs: list[dict[str, float]],
) -> float:
    d = mean_knn_distance(target_attrs, past_attrs, k=3)
    if d is None:
        return 0.0
    return max(0.0, 1.0 - min(1.0, d / CONF_SIM_D_MAX))


def decisiveness_term(probabilities: list[float]) -> float:
    m = len(probabilities)
    if m <= 1:
        return 1.0
    total = 0.0
    for p in probabilities:
        if p > 0:
            total -= p * math.log(p)
    h_max = math.log(m)
    if h_max <= 0:
        return 1.0
    return max(0.0, 1.0 - (total / h_max))


def sample_support_term(n_decisions: int) -> float:
    return 1.0 - math.exp(-max(0, n_decisions) / 10.0)


def combine(
    *,
    scenario_similarity: float,
    decisiveness: float,
    sample_support: float,
    n_decisions: int,
) -> tuple[float, dict[str, float]]:
    raw = (
        CONF_WEIGHT_SIM * scenario_similarity
        + CONF_WEIGHT_DECISIVE * decisiveness
        + CONF_WEIGHT_SAMPLE * sample_support
    )
    capped = raw
    if n_decisions < 5:
        capped = min(raw, CONF_CAP_UNDER_5)
    elif n_decisions < 10:
        capped = min(raw, CONF_CAP_UNDER_10)
    return round(capped, 4), {
        "scenario_similarity": round(scenario_similarity, 4),
        "decisiveness": round(decisiveness, 4),
        "sample_support": round(sample_support, 4),
    }


def band_for(confidence: float) -> str:
    if confidence >= CONF_BAND_HIGH:
        return "HIGH"
    if confidence >= CONF_BAND_MEDIUM:
        return "MEDIUM"
    return "LOW"


__all__ = [
    "similarity_term",
    "decisiveness_term",
    "sample_support_term",
    "combine",
    "band_for",
]