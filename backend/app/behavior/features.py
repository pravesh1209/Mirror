"""Raw per-scenario metrics -> normalized 9-axis feature vector.

Every feature is in [0, 1] or None. A feature is None when there is not
enough signal to say anything. That is honest, not a bug.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean, pstdev
from typing import Iterable

from .constants import (
    FEATURE_CONF_HIGH_N,
    FEATURE_CONF_HIGH_SCORE,
    FEATURE_CONF_MED_N,
    FEATURE_CONF_MED_SCORE,
    FEATURE_NAMES,
    FEATURE_STABILITY_SPREAD,
    K_RECON,
    K_SPEED_MS_PER_OPTION,
    K_TIME_PRESSURE_DELTA,
)
from .events import RawMetrics, aggregate_speed, sat


@dataclass
class FeatureResult:
    features: dict[str, float | None] = field(default_factory=dict)
    n_per_axis: dict[str, int] = field(default_factory=dict)
    exposures: dict[str, list[float]] = field(default_factory=dict)


def _safe_mean(xs: Iterable[float | None]) -> tuple[float | None, int]:
    vals = [float(x) for x in xs if x is not None]
    return (mean(vals), len(vals)) if vals else (None, 0)


def compute_features(
    per_scenario: list[RawMetrics],
    *,
    consistency: float | None = None,
) -> FeatureResult:
    """Compute the 9-axis feature vector from per-scenario raw metrics.

    `consistency` is computed outside this function (needs the choice model)
    and passed in so the orchestration stays linear.
    """
    r = FeatureResult()
    n = len(per_scenario)

    # ---- decision_speed -----------------------------------------------
    speeds = [m.speed_raw for m in per_scenario if m.speed_raw is not None]
    med = aggregate_speed([s for s in speeds if s is not None])
    if med is None:
        r.features["decision_speed"] = None
        r.n_per_axis["decision_speed"] = 0
    else:
        val = 1.0 - sat(med, K_SPEED_MS_PER_OPTION)
        r.features["decision_speed"] = round(max(0.0, min(1.0, val)), 4)
        r.n_per_axis["decision_speed"] = len(speeds)
        r.exposures["decision_speed"] = [float(s) for s in speeds]

    # ---- exploration --------------------------------------------------
    expl, n_expl = _safe_mean(m.exploration_raw for m in per_scenario)
    info, n_info = _safe_mean(m.info_rate_raw for m in per_scenario)
    if n == 0 or (n_expl == 0 and n_info == 0):
        r.features["exploration"] = None
        r.n_per_axis["exploration"] = 0
    else:
        e = expl if expl is not None else 0.0
        i = info if info is not None else 0.0
        r.features["exploration"] = round(0.6 * e + 0.4 * i, 4)
        r.n_per_axis["exploration"] = n
        r.exposures["exploration"] = [
            float(m.exploration_raw) for m in per_scenario if m.exploration_raw is not None
        ]

    # ---- evidence_seeking ---------------------------------------------
    if n == 0:
        r.features["evidence_seeking"] = None
        r.n_per_axis["evidence_seeking"] = 0
    else:
        info_mean = info if info is not None else 0.0
        opened_any = sum(1 for m in per_scenario if m.n_info_opened >= 1) / float(n)
        r.features["evidence_seeking"] = round(0.5 * info_mean + 0.5 * opened_any, 4)
        r.n_per_axis["evidence_seeking"] = n
        r.exposures["evidence_seeking"] = [
            float(m.info_rate_raw) for m in per_scenario if m.info_rate_raw is not None
        ]

    # ---- reconsideration ----------------------------------------------
    recon_mean, n_recon = _safe_mean(m.reconsider_raw for m in per_scenario)
    if recon_mean is None:
        r.features["reconsideration"] = None
        r.n_per_axis["reconsideration"] = 0
    else:
        r.features["reconsideration"] = round(sat(recon_mean, K_RECON), 4)
        r.n_per_axis["reconsideration"] = n_recon
        r.exposures["reconsideration"] = [
            float(m.reconsider_raw) for m in per_scenario if m.reconsider_raw is not None
        ]

    # ---- risk_tolerance / novelty_seeking / uncertainty_tolerance -----
    for axis, attr in (
        ("risk_tolerance", "risk_exposure"),
        ("novelty_seeking", "novelty_exposure"),
        ("uncertainty_tolerance", "uncertainty_exposure"),
    ):
        vals = [getattr(m, attr) for m in per_scenario if getattr(m, attr) is not None]
        if not vals:
            r.features[axis] = None
            r.n_per_axis[axis] = 0
        else:
            r.features[axis] = round(mean(vals), 4)
            r.n_per_axis[axis] = len(vals)
            r.exposures[axis] = [float(v) for v in vals]

    # ---- adaptability --------------------------------------------------
    adapt_vals = [m.adaptation for m in per_scenario if m.adaptation is not None]
    if not adapt_vals:
        r.features["adaptability"] = None
        r.n_per_axis["adaptability"] = 0
    else:
        r.features["adaptability"] = round(mean(adapt_vals), 4)
        r.n_per_axis["adaptability"] = len(adapt_vals)
        r.exposures["adaptability"] = [float(v) for v in adapt_vals]

    # ---- consistency ---------------------------------------------------
    if consistency is None:
        r.features["consistency"] = None
        r.n_per_axis["consistency"] = 0
    else:
        r.features["consistency"] = round(max(0.0, min(1.0, float(consistency))), 4)
        r.n_per_axis["consistency"] = n

    # ---- time_pressure_response ---------------------------------------
    # Exposed as a separate axis? The spec listed it as a feature. We keep
    # it internal to the profile narrative because it needs >=2 low and >=2
    # high pressure scenarios; exposing it as a radar spoke risks a null
    # spoke that most users never fill.
    low_speeds = [
        m.speed_raw for m in per_scenario
        if m.speed_raw is not None and m.time_pressure < 0.4
    ]
    high_speeds = [
        m.speed_raw for m in per_scenario
        if m.speed_raw is not None and m.time_pressure > 0.6
    ]
    if len(low_speeds) >= 2 and len(high_speeds) >= 2:
        delta = mean(high_speeds) - mean(low_speeds)  # positive = slower under pressure
        tp = 0.5 + 0.5 * max(-1.0, min(1.0, delta / K_TIME_PRESSURE_DELTA))
        r.features["time_pressure_response"] = round(tp, 4)
        r.n_per_axis["time_pressure_response"] = len(low_speeds) + len(high_speeds)
        r.exposures["time_pressure_response"] = [
            float(x) for x in (low_speeds + high_speeds)
        ]
    else:
        r.features["time_pressure_response"] = None
        r.n_per_axis["time_pressure_response"] = 0

    # Ensure every public axis is present in the dict
    for name in FEATURE_NAMES:
        r.features.setdefault(name, None)
        r.n_per_axis.setdefault(name, 0)

    return r


# ----------------------------------------------------------------------
# Per-feature confidence
# ----------------------------------------------------------------------
def feature_confidence(n: int, exposures: list[float]) -> dict:
    """Return {level, score, n} for one feature axis."""
    if n <= 0:
        return {"level": "LOW", "score": 0.0, "n": 0}

    if len(exposures) >= 2:
        sigma = pstdev(exposures)
    else:
        sigma = 0.0
    stability = 1.0 - min(1.0, sigma / FEATURE_STABILITY_SPREAD)

    import math
    score = (1.0 - math.exp(-n / 4.0)) * stability

    if score >= FEATURE_CONF_HIGH_SCORE and n >= FEATURE_CONF_HIGH_N:
        level = "HIGH"
    elif score >= FEATURE_CONF_MED_SCORE and n >= FEATURE_CONF_MED_N:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {"level": level, "score": round(score, 4), "n": int(n)}


def confidence_map(result: FeatureResult) -> dict[str, dict]:
    return {
        name: feature_confidence(result.n_per_axis.get(name, 0), result.exposures.get(name, []))
        for name in FEATURE_NAMES
    }


__all__ = ["FeatureResult", "compute_features", "feature_confidence", "confidence_map"]