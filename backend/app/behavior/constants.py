"""Tunable constants for the MIRROR behavior engine.

These are stated, documented constants — not learned parameters.
They are referenced in docs/behavior-model.md and are intentionally exposed
here so a reviewer can see exactly what MIRROR assumes.
"""
from __future__ import annotations

# Normalization reference points ("the value at which a measurement is ~63%
# of the way to maximum observed interest").
K_SPEED_MS_PER_OPTION = 8000.0   # ms per option; higher = slower
K_RECON = 1.0                    # reversals + revisits per unique option viewed
K_TIME_PRESSURE_DELTA = 6000.0   # ms difference in speed between low/high pressure

# Choice model
CHOICE_TAU = 0.5                 # softmax temperature
CHOICE_L2_LAMBDA = 0.5           # L2 regularization strength
CHOICE_FEATURE_ORDER = [
    "risk",
    "speed_aversion",     # = 1 - time_cost
    "cost_aversion",      # = 1 - money_cost
    "novelty",
    "uncertainty",
    "info_availability",
    "reward",
]

# Confidence
CONF_SIM_D_MAX = 1.2             # scenario space distance ceiling
CONF_WEIGHT_SIM = 0.40
CONF_WEIGHT_DECISIVE = 0.35
CONF_WEIGHT_SAMPLE = 0.25
CONF_BAND_HIGH = 0.70
CONF_BAND_MEDIUM = 0.45

# Per-feature confidence bands
FEATURE_CONF_HIGH_SCORE = 0.66
FEATURE_CONF_HIGH_N = 6
FEATURE_CONF_MED_SCORE = 0.33
FEATURE_CONF_MED_N = 3
FEATURE_STABILITY_SPREAD = 0.35

# Cold start guards
MIN_SAMPLES_TO_PREDICT = 1
CONF_CAP_UNDER_5 = 0.35
CONF_CAP_UNDER_10 = 0.65
CALIBRATION_MIN_RESOLVED = 10

# Feature names — order matters for UI display
FEATURE_NAMES = [
    "decision_speed",
    "exploration",
    "risk_tolerance",
    "evidence_seeking",
    "reconsideration",
    "consistency",
    "novelty_seeking",
    "uncertainty_tolerance",
    "adaptability",
]

# Scenario-attribute axes used by similarity
SCENARIO_AXES = [
    "difficulty",
    "risk",
    "uncertainty",
    "time_pressure",
    "novelty",
    "reward",
    "information_availability",
]
