"""Event stream -> per-scenario raw measurements.

This module is intentionally pure: it receives lists of event dicts and
option/scenario/decision data and returns numbers. No DB access, no LLM.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from statistics import median
from typing import Iterable, Mapping

from .constants import K_RECON, K_SPEED_MS_PER_OPTION

# ----------------------------------------------------------------------
# Event type names we understand. Unknown types are ignored.
# ----------------------------------------------------------------------
EV_STARTED = "scenario_started"
EV_OPTION_VIEWED = "option_viewed"
EV_OPTION_REVISITED = "option_revisited"
EV_OPTION_SELECTED = "option_selected"
EV_INFO_OPENED = "information_opened"
EV_INFO_CLOSED = "information_closed"
EV_DECISION_CHANGED = "decision_changed"
EV_CONFIDENCE_CHANGED = "confidence_changed"
EV_HINT_REQUESTED = "hint_requested"
EV_REASONING_SUBMITTED = "reasoning_submitted"
EV_DECISION_SUBMITTED = "decision_submitted"
EV_SCENARIO_COMPLETED = "scenario_completed"

INFO_SLOTS_ASSUMED = 4  # number of info items a scenario "offers" at information_availability=1.0


@dataclass
class RawMetrics:
    """Everything we can measure from a single completed scenario."""

    latency_ms: int = 0
    first_touch_ms: int | None = None
    n_options: int = 0
    n_unique_viewed: int = 0
    n_views: int = 0
    n_info_opened: int = 0
    n_info_available: int = 0
    n_reversals: int = 0
    n_revisits: int = 0
    self_confidence: float | None = None
    reasoning_words: int = 0

    first_option_viewed: str | None = None
    final_option_label: str | None = None

    # Derived (raw, not yet normalized)
    speed_raw: float | None = None
    exploration_raw: float | None = None
    info_rate_raw: float | None = None
    reconsider_raw: float | None = None

    # Choice exposures (only when the scenario offered a spread)
    risk_exposure: float | None = None
    novelty_exposure: float | None = None
    uncertainty_exposure: float | None = None

    # Adaptability (only when scenario.has_reveal)
    adaptation: float | None = None

    # Which scenario attributes were present (for downstream filtering)
    time_pressure: float = 0.5
    has_reveal: bool = False

    # Extras for auditing
    extras: dict = field(default_factory=dict)


def _t_of(event: Mapping) -> int:
    return int(event.get("relative_time_ms") or 0)


def _type_of(event: Mapping) -> str:
    return str(event.get("event_type") or "")


def _payload(event: Mapping) -> dict:
    p = event.get("payload")
    return p if isinstance(p, dict) else {}


def _sorted_events(events: Iterable[Mapping]) -> list[Mapping]:
    return sorted(events, key=_t_of)


def metrics_from_events(
    events: Iterable[Mapping],
    *,
    n_options: int,
    option_label_by_id: Mapping[str, str],
    time_pressure: float,
    has_reveal: bool,
    information_availability: float,
) -> RawMetrics:
    """Compute raw per-scenario metrics from events alone."""
    evs = _sorted_events(events)
    m = RawMetrics(
        n_options=n_options,
        time_pressure=time_pressure,
        has_reveal=has_reveal,
    )
    m.n_info_available = max(1, int(round(information_availability * INFO_SLOTS_ASSUMED)))

    start_ts: int | None = None
    decision_ts: int | None = None
    unique_viewed: set[str] = set()
    info_ids: set[str] = set()
    reveal_ts: int | None = None
    choice_change_after_reveal = False
    choice_before_reveal: str | None = None
    last_conf: float | None = None

    for e in evs:
        t = _t_of(e)
        et = _type_of(e)
        opt_id = e.get("option_id")
        p = _payload(e)

        if et == EV_STARTED:
            start_ts = t
            continue

        if et == EV_OPTION_VIEWED:
            if opt_id:
                if m.first_option_viewed is None and opt_id in option_label_by_id:
                    m.first_option_viewed = option_label_by_id[opt_id]
                unique_viewed.add(opt_id)
                m.n_views += 1
                if m.first_touch_ms is None and start_ts is not None:
                    m.first_touch_ms = t - start_ts
            continue

        if et == EV_OPTION_REVISITED:
            m.n_revisits += 1
            if opt_id:
                unique_viewed.add(opt_id)
            continue

        if et == EV_INFO_OPENED:
            info_id = p.get("info_id") or opt_id or f"_anon_{t}"
            info_ids.add(str(info_id))
            continue

        if et == EV_INFO_CLOSED:
            continue

        if et == EV_DECISION_CHANGED:
            m.n_reversals += 1
            new_label = None
            if opt_id and opt_id in option_label_by_id:
                new_label = option_label_by_id[opt_id]
            if has_reveal and reveal_ts is not None and t > reveal_ts:
                choice_change_after_reveal = True
            elif not has_reveal or reveal_ts is None:
                # Before any reveal, track the leaning
                if new_label:
                    choice_before_reveal = new_label
            continue

        if et == EV_CONFIDENCE_CHANGED:
            try:
                val = float(p.get("value", p.get("confidence", 0.0)))
                if val > 1.0:
                    val = val / 100.0
                last_conf = max(0.0, min(1.0, val))
            except (TypeError, ValueError):
                pass
            continue

        if et == EV_REASONING_SUBMITTED:
            text = str(p.get("text") or "")
            m.reasoning_words = len(text.split())
            continue

        if et == EV_DECISION_SUBMITTED:
            decision_ts = t
            continue

        if et == EV_SCENARIO_COMPLETED:
            if decision_ts is None:
                decision_ts = t
            continue

    # latency: prefer decision_submitted, else last event
    end_ts = decision_ts if decision_ts is not None else (evs[-1] and _t_of(evs[-1]))
    if start_ts is not None and end_ts is not None:
        m.latency_ms = max(0, int(end_ts - start_ts))

    m.n_unique_viewed = len(unique_viewed)
    m.n_info_opened = len(info_ids)
    m.self_confidence = last_conf

    # ---- derived raw measures -----------------------------------------
    if m.latency_ms > 0 and m.n_options > 0:
        m.speed_raw = m.latency_ms / float(m.n_options)

    if m.n_options > 0:
        m.exploration_raw = min(1.0, m.n_unique_viewed / float(m.n_options))

    m.info_rate_raw = min(1.0, m.n_info_opened / float(max(1, m.n_info_available)))

    if m.n_unique_viewed > 0:
        m.reconsider_raw = (m.n_reversals + m.n_revisits) / float(m.n_unique_viewed)

    # adaptation: did the user change after mid-scenario reveal?
    if has_reveal:
        if reveal_ts is None:
            # nothing to compare against; treat as no measurable change
            m.adaptation = None
        else:
            m.adaptation = 1.0 if choice_change_after_reveal else 0.0

    return m


def apply_choice_exposures(
    m: RawMetrics,
    *,
    chosen_label: str | None,
    options: list[Mapping],
) -> RawMetrics:
    """Fill in risk/novelty/uncertainty exposures from option attributes.

    Each exposure is a normalized position in [0, 1]:
        (attr(chosen) - min(attr)) / (max(attr) - min(attr))
    Returned as None when the scenario did not offer a meaningful spread.
    """
    if not chosen_label or not options:
        return m

    chosen = next((o for o in options if o.get("label") == chosen_label), None)
    if chosen is None:
        return m

    attrs = chosen.get("attributes") or {}
    get = lambda key: float(attrs.get(key, 0.5))

    def spread(key: str) -> tuple[float, float]:
        vals = [float((o.get("attributes") or {}).get(key, 0.5)) for o in options]
        return min(vals), max(vals)

    def exposure(key: str) -> float | None:
        lo, hi = spread(key)
        if hi - lo < 0.15:
            return None
        return (get(key) - lo) / (hi - lo)

    m.risk_exposure = exposure("risk")
    m.novelty_exposure = exposure("novelty")
    m.uncertainty_exposure = exposure("uncertainty")
    return m


def sat(x: float | None, k: float) -> float:
    """Saturating exponential: 0 at x<=0, approaches 1 as x grows."""
    if x is None:
        return 0.0
    x = max(0.0, float(x))
    import math
    return 1.0 - math.exp(-x / k) if k > 0 else 0.0


def aggregate_speed(speeds: list[float]) -> float | None:
    return None if not speeds else float(median(speeds))


__all__ = [
    "RawMetrics",
    "metrics_from_events",
    "apply_choice_exposures",
    "sat",
    "aggregate_speed",
    "EV_STARTED",
    "EV_OPTION_VIEWED",
    "EV_OPTION_REVISITED",
    "EV_OPTION_SELECTED",
    "EV_INFO_OPENED",
    "EV_INFO_CLOSED",
    "EV_DECISION_CHANGED",
    "EV_CONFIDENCE_CHANGED",
    "EV_HINT_REQUESTED",
    "EV_REASONING_SUBMITTED",
    "EV_DECISION_SUBMITTED",
    "EV_SCENARIO_COMPLETED",
]