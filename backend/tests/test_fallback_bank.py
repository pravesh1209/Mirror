"""Tests for the deterministic scenario bank."""
from __future__ import annotations

from app.ai.schemas import GeneratedScenario
from app.simulation import fallback_bank as fb
from app.simulation.scenarios_core import SCENARIOS


def test_bank_has_twelve():
    assert len(SCENARIOS) == 12


def test_every_scenario_validates_against_ai_schema():
    for s in SCENARIOS:
        model = GeneratedScenario.model_validate(s)
        assert 2 <= len(model.options) <= 5


def test_all_labels_unique_within_scenario():
    for s in SCENARIOS:
        labels = [o["label"] for o in s["options"]]
        assert len(labels) == len(set(labels)), s["title"]


def test_at_least_two_scenarios_have_reveal():
    n = sum(1 for s in SCENARIOS if s["has_reveal"])
    assert n >= 2


def test_at_least_one_scenario_has_time_limit():
    n = sum(1 for s in SCENARIOS if s["time_limit_sec"])
    assert n >= 1


def test_domains_are_known():
    allowed = {"education", "career", "everyday", "finance", "productivity"}
    for s in SCENARIOS:
        assert s["domain"] in allowed, s["domain"]


def test_pick_for_calibration_returns_none_when_exhausted():
    used = {s["title"] for s in SCENARIOS}
    assert fb.pick_for_calibration(used) is None


def test_pick_targeting_axis_returns_something():
    for axis in [
        "adaptability", "risk_tolerance", "novelty_seeking",
        "time_pressure_response", "uncertainty_tolerance",
    ]:
        s = fb.pick_targeting_axis(axis)
        assert isinstance(s, dict) and "title" in s


def test_all_scenarios_are_deep_copies():
    a = fb.all_scenarios()
    a[0]["title"] = "MUTATED"
    b = fb.all_scenarios()
    assert b[0]["title"] != "MUTATED"