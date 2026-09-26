"""What-if re-scoring.

Given a scenario and a set of attribute overrides, produce a new prediction
using the current profile. Pure computation; no LLM.
"""
from __future__ import annotations

from .engine import PredictionComputation, compute


def apply_overrides(
    *,
    scenario_attrs: dict[str, float],
    option_dicts: list[dict],
    overrides: dict[str, float],
) -> tuple[dict[str, float], list[dict]]:
    """Return (new_scenario_attrs, new_option_dicts)."""
    new_sc = dict(scenario_attrs)
    for k, v in overrides.items():
        if k in new_sc and isinstance(v, (int, float)):
            new_sc[k] = max(0.0, min(1.0, float(v)))

    new_opts: list[dict] = []
    for o in option_dicts:
        attrs = dict(o.get("attributes") or {})
        # scenario-level overrides propagate to option-level attributes
        if "time_pressure" in overrides:
            delta = float(overrides["time_pressure"]) - float(scenario_attrs.get("time_pressure", 0.5))
            attrs["time_cost"] = max(0.0, min(1.0, float(attrs.get("time_cost", 0.5)) + delta * 0.5))
        if "uncertainty" in overrides:
            delta = float(overrides["uncertainty"]) - float(scenario_attrs.get("uncertainty", 0.5))
            attrs["uncertainty"] = max(0.0, min(1.0, float(attrs.get("uncertainty", 0.5)) + delta))
        if "risk" in overrides:
            delta = float(overrides["risk"]) - float(scenario_attrs.get("risk", 0.5))
            attrs["risk"] = max(0.0, min(1.0, float(attrs.get("risk", 0.5)) + delta))
        if "novelty" in overrides:
            delta = float(overrides["novelty"]) - float(scenario_attrs.get("novelty", 0.5))
            attrs["novelty"] = max(0.0, min(1.0, float(attrs.get("novelty", 0.5)) + delta))
        new_opts.append({"label": o["label"], "attributes": attrs})

    return new_sc, new_opts


def reason_text(overrides: dict[str, float]) -> str:
    keys = sorted(overrides.keys())
    if not keys:
        return "No attribute changed; the prediction is identical."
    parts = ", ".join(keys)
    return (
        f"MIRROR re-scored the scenario with {parts} overridden. "
        f"The change reflects how your historical behavior shifts on the "
        f"affected axes."
    )


__all__ = ["apply_overrides", "reason_text", "PredictionComputation", "compute"]