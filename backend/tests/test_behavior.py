"""Golden-path tests for the behavior engine."""
from __future__ import annotations

import numpy as np
import pytest

from app.behavior import choice_model as cm
from app.behavior import features as feat
from app.behavior import scoring as sc
from app.behavior import similarity as sim
from app.behavior.events import RawMetrics, apply_choice_exposures, metrics_from_events


# ----------------------------------------------------------------------
# events.py
# ----------------------------------------------------------------------
def _ev(t, typ, opt=None, payload=None):
    return {
        "event_type": typ,
        "option_id": opt,
        "payload": payload or {},
        "relative_time_ms": t,
    }


def test_metrics_basic_flow():
    events = [
        _ev(0, "scenario_started"),
        _ev(500, "option_viewed", "o1"),
        _ev(1500, "option_viewed", "o2"),
        _ev(1800, "information_opened", None, {"info_id": "i1"}),
        _ev(2400, "decision_changed", "o1"),
        _ev(3000, "decision_submitted", "o1"),
        _ev(3000, "scenario_completed"),
    ]
    label_by_id = {"o1": "A", "o2": "B"}
    m = metrics_from_events(
        events,
        n_options=2,
        option_label_by_id=label_by_id,
        time_pressure=0.3,
        has_reveal=False,
        information_availability=0.5,
    )
    assert m.latency_ms == 3000
    assert m.first_option_viewed == "A"
    assert m.n_unique_viewed == 2
    assert m.n_info_opened == 1
    assert m.n_reversals == 1
    assert m.speed_raw == pytest.approx(1500.0)
    assert m.exploration_raw == pytest.approx(1.0)
    assert m.info_rate_raw == pytest.approx(0.5)  # 1 / (0.5 * 4) = 0.5
    assert m.reconsider_raw == pytest.approx(1.0 / 2.0)


def test_exposures_normalized():
    opts = [
        {"label": "A", "attributes": {"risk": 0.1, "novelty": 0.9, "uncertainty": 0.5}},
        {"label": "B", "attributes": {"risk": 0.9, "novelty": 0.2, "uncertainty": 0.4}},
        {"label": "C", "attributes": {"risk": 0.5, "novelty": 0.5, "uncertainty": 0.1}},
    ]
    m = RawMetrics()
    apply_choice_exposures(m, chosen_label="B", options=opts)

    # risk: values {0.1, 0.9, 0.5} -> min=0.1, max=0.9 -> spread=0.8 >= 0.15
    # chosen B has risk=0.9 -> exposure = (0.9 - 0.1) / 0.8 = 1.0
    assert m.risk_exposure == pytest.approx(1.0)

    # novelty: values {0.9, 0.2, 0.5} -> min=0.2, max=0.9 -> spread=0.7
    # chosen B has novelty=0.2 -> exposure = (0.2 - 0.2) / 0.7 = 0.0
    assert m.novelty_exposure == pytest.approx(0.0)

    # uncertainty: values {0.5, 0.4, 0.1} -> min=0.1, max=0.5 -> spread=0.4
    # chosen B has uncertainty=0.4 -> exposure = (0.4 - 0.1) / 0.4 = 0.75
    assert m.uncertainty_exposure == pytest.approx(0.75)


def test_exposure_none_when_spread_too_small():
    """All options within 0.15 of each other on an axis => no exposure recorded."""
    opts = [
        {"label": "A", "attributes": {"risk": 0.48}},
        {"label": "B", "attributes": {"risk": 0.50}},
        {"label": "C", "attributes": {"risk": 0.52}},
    ]
    m = RawMetrics()
    apply_choice_exposures(m, chosen_label="B", options=opts)
    assert m.risk_exposure is None


# ----------------------------------------------------------------------
# choice_model.py
# ----------------------------------------------------------------------
def _scenario(option_attrs: list[dict]) -> np.ndarray:
    return np.stack([cm.option_vector(a) for a in option_attrs])


def test_softmax_probs_sum_to_one():
    X = _scenario(
        [
            {"risk": 0.1, "reward": 0.9},
            {"risk": 0.9, "reward": 0.1},
        ]
    )
    w = np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    p = cm.predict_proba(w, X)
    assert p.sum() == pytest.approx(1.0)
    assert p[1] > p[0]  # higher risk weight => option B more likely


def test_fit_recovers_direction():
    # A synthetic user who always picks the highest-novelty option
    rows = []
    chosen = []
    for _ in range(8):
        attrs = [
            {"novelty": 0.9, "risk": 0.5, "reward": 0.5},
            {"novelty": 0.1, "risk": 0.5, "reward": 0.5},
            {"novelty": 0.5, "risk": 0.5, "reward": 0.5},
        ]
        rows.append(_scenario(attrs))
        chosen.append(0)
    ds = cm.ChoiceDataset(scenarios=rows, chosen_indices=chosen, option_labels=[["A", "B", "C"]] * 8)
    w = cm.fit(ds, iterations=600, lr=0.1)
    wd = cm.weights_as_dict(w)
    assert wd["novelty"] > wd["risk"]


def test_consistency_none_when_too_few():
    ds = cm.ChoiceDataset(scenarios=[], chosen_indices=[], option_labels=[])
    assert cm.consistency_score(np.zeros(7), ds) is None


# ----------------------------------------------------------------------
# features.py
# ----------------------------------------------------------------------
def test_features_all_none_on_empty():
    r = feat.compute_features([])
    for k, v in r.features.items():
        assert v is None, f"{k} should be None on empty input"
    assert all(n == 0 for n in r.n_per_axis.values())


def test_features_bounds():
    rows = []
    for i in range(6):
        rows.append(
            RawMetrics(
                latency_ms=4000,
                n_options=3,
                n_unique_viewed=3,
                n_info_opened=2,
                n_info_available=4,
                n_reversals=1,
                n_revisits=0,
                speed_raw=4000 / 3.0,
                exploration_raw=1.0,
                info_rate_raw=0.5,
                reconsider_raw=1.0 / 3.0,
                risk_exposure=0.7,
                novelty_exposure=0.8,
                uncertainty_exposure=0.4,
                time_pressure=0.3,
                has_reveal=(i % 2 == 0),
                adaptation=1.0 if i % 2 == 0 else None,
            )
        )
    r = feat.compute_features(rows, consistency=0.6)
    for name in feat.FEATURE_NAMES:
        v = r.features.get(name)
        if v is not None:
            assert 0.0 <= v <= 1.0, f"{name}={v} out of [0,1]"
    assert r.features["risk_tolerance"] == pytest.approx(0.7)
    assert r.features["novelty_seeking"] == pytest.approx(0.8)
    assert r.features["consistency"] == pytest.approx(0.6)


def test_confidence_bands():
    assert feat.feature_confidence(0, [])["level"] == "LOW"
    assert feat.feature_confidence(2, [0.5, 0.5])["level"] == "LOW"
    assert feat.feature_confidence(8, [0.5] * 8)["level"] == "HIGH"
    assert feat.feature_confidence(4, [0.1, 0.9, 0.1, 0.9])["level"] == "LOW"


# ----------------------------------------------------------------------
# similarity.py
# ----------------------------------------------------------------------
def test_distance_bounds_and_identity():
    a = {k: 0.5 for k in ["difficulty", "risk", "uncertainty", "time_pressure",
                          "novelty", "reward", "information_availability"]}
    b = dict(a)
    assert sim.scenario_distance(a, b) == pytest.approx(0.0)
    b["risk"] = 1.0
    assert 0.0 < sim.scenario_distance(a, b) <= 1.0


def test_knn_distance_none_when_empty():
    assert sim.mean_knn_distance({"risk": 0.5}, []) is None


# ----------------------------------------------------------------------
# scoring.py
# ----------------------------------------------------------------------
def test_brier_and_correct():
    dist = {"A": 0.7, "B": 0.2, "C": 0.1}
    assert sc.choice_correct(dist, "A") is True
    assert sc.choice_correct(dist, "B") is False
    assert sc.top2_correct(dist, "B") is True
    assert sc.brier_score(dist, "A") == pytest.approx(0.14, abs=1e-6)


def test_style():
    assert sc.predicted_style(3, 3, 5000, 1000) == "explore_first"
    assert sc.predicted_style(1, 3, 4000, 3000) == "commit_fast"
    assert sc.predicted_style(1, 3, 20000, 1000) == "balanced"