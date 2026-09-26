"""Detect blind spots in MIRROR's model of a user.

A blind spot is any axis where:
  * fewer than 3 observations exist (low_n)
  * observations exist but vary wildly (high_variance)
  * the scenarios completed never exercised the condition (unobserved_condition)

We use the current profile's confidence map and the per-scenario feature rows.
Nothing here is learned; every threshold is a stated constant.
"""
from __future__ import annotations

import logging
from statistics import pstdev

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import BlindSpot, BehaviorFeature, Scenario, Decision
from ..behavior.constants import FEATURE_NAMES

log = logging.getLogger("mirror.blindspots.detector")

LOW_N_THRESHOLD = 3
HIGH_VARIANCE_THRESHOLD = 0.35

_AXIS_STATEMENTS: dict[str, str] = {
    "adaptability": "How you respond when new information arrives mid-decision",
    "risk_tolerance": "How you weigh risk when a scenario offers a spread",
    "novelty_seeking": "How you weigh familiar vs unfamiliar options",
    "uncertainty_tolerance": "How much missing information you accept before deciding",
    "reconsideration": "How often you revisit or reverse a choice",
    "time_pressure_response": "How your behavior changes under time pressure",
    "evidence_seeking": "Whether you open extra information before deciding",
    "exploration": "Whether you inspect more than one option",
    "consistency": "Whether a single stable policy describes your choices",
    "decision_speed": "How quickly you tend to decide",
}

_AXIS_PREFERRED_SCENARIOS: dict[str, list[str]] = {
    "adaptability": ["An unplanned course opportunity", "An unexpected internal move"],
    "uncertainty_tolerance": ["An unfamiliar investment", "Two job offers, very different shapes"],
    "risk_tolerance": ["Two job offers, very different shapes", "Where the extra $500 goes"],
    "novelty_seeking": ["An unplanned course opportunity", "An unfamiliar investment"],
    "time_pressure_response": ["Getting across town", "A day with too many open threads"],
}


def _statement_for(axis: str) -> str:
    return _AXIS_STATEMENTS.get(axis, f"Observed behavior on {axis}")


async def detect_blind_spots(
    db: AsyncSession,
    *,
    user_id: str,
    profile_confidence: dict[str, dict],
) -> list[dict]:
    """Return a list of blind-spot dicts. Does not persist."""
    # Load per-scenario feature rows for variance analysis
    q = await db.execute(
        select(BehaviorFeature).where(BehaviorFeature.user_id == user_id)
    )
    rows = list(q.scalars().all())

    # Also check which scenario *conditions* have been exercised
    decisions_q = await db.execute(select(Decision).where(Decision.user_id == user_id))
    decisions = list(decisions_q.scalars().all())
    scenario_ids = {d.scenario_id for d in decisions}

    reveal_scenarios_seen = 0
    time_pressure_scenarios_seen = 0
    high_risk_scenarios_seen = 0
    if scenario_ids:
        sc_q = await db.execute(select(Scenario).where(Scenario.id.in_(scenario_ids)))
        for sc in sc_q.scalars().all():
            if sc.has_reveal:
                reveal_scenarios_seen += 1
            if sc.time_pressure > 0.6:
                time_pressure_scenarios_seen += 1
            if sc.risk > 0.6:
                high_risk_scenarios_seen += 1

    out: list[dict] = []

    for axis in FEATURE_NAMES:
        c = profile_confidence.get(axis) or {}
        n = int(c.get("n", 0))

        if n < LOW_N_THRESHOLD:
            severity = round(1.0 - (n / LOW_N_THRESHOLD) * 0.5, 4)
            out.append(
                {
                    "axis": axis,
                    "kind": "low_n",
                    "severity": severity,
                    "evidence_count": n,
                    "statement": _statement_for(axis),
                }
            )
            continue

        # variance analysis over exposure values
        exposures = [
            (r.feature_vector or {}).get(axis)
            for r in rows
            if (r.feature_vector or {}).get(axis) is not None
        ]
        if len(exposures) >= 3:
            sigma = pstdev(exposures)
            if sigma > HIGH_VARIANCE_THRESHOLD:
                out.append(
                    {
                        "axis": axis,
                        "kind": "high_variance",
                        "severity": round(min(1.0, sigma / 0.5), 4),
                        "evidence_count": len(exposures),
                        "statement": _statement_for(axis),
                    }
                )

    # Unobserved conditions — checked independent of per-axis confidence
    if reveal_scenarios_seen == 0:
        out.append(
            {
                "axis": "adaptability",
                "kind": "unobserved_condition",
                "severity": 0.9,
                "evidence_count": 0,
                "statement": "How you respond when information changes mid-decision",
            }
        )
    if time_pressure_scenarios_seen == 0:
        out.append(
            {
                "axis": "time_pressure_response",
                "kind": "unobserved_condition",
                "severity": 0.85,
                "evidence_count": 0,
                "statement": "How your behavior changes under time pressure",
            }
        )
    if high_risk_scenarios_seen == 0:
        out.append(
            {
                "axis": "risk_tolerance",
                "kind": "unobserved_condition",
                "severity": 0.7,
                "evidence_count": 0,
                "statement": "How you weigh risk when a scenario offers a spread",
            }
        )

    # Deduplicate by axis, keeping highest severity
    best: dict[str, dict] = {}
    for item in out:
        prev = best.get(item["axis"])
        if prev is None or item["severity"] > prev["severity"]:
            best[item["axis"]] = item

    ranked = sorted(best.values(), key=lambda x: x["severity"], reverse=True)
    return ranked


async def persist_blind_spots(
    db: AsyncSession,
    *,
    user_id: str,
    detections: list[dict],
) -> None:
    """Replace open blind-spot rows for this user with the current set.

    Resolved spots (no longer detected) are marked resolved rather than
    deleted, so the timeline can show progress.
    """
    existing_q = await db.execute(
        select(BlindSpot).where(
            BlindSpot.user_id == user_id,
            BlindSpot.status == "open",
        )
    )
    existing = {b.axis: b for b in existing_q.scalars().all()}
    detected_axes = {d["axis"] for d in detections}

    from ..db import utcnow
    for axis, row in existing.items():
        if axis not in detected_axes:
            row.status = "resolved"
            row.resolved_at = utcnow()

    for item in detections:
        row = existing.get(item["axis"])
        if row is None:
            db.add(
                BlindSpot(
                    user_id=user_id,
                    axis=item["axis"],
                    kind=item["kind"],
                    severity=item["severity"],
                    evidence_count=item["evidence_count"],
                    status="open",
                )
            )
        else:
            row.kind = item["kind"]
            row.severity = item["severity"]
            row.evidence_count = item["evidence_count"]

    await db.flush()


async def open_blind_spots(db: AsyncSession, user_id: str) -> list[BlindSpot]:
    q = await db.execute(
        select(BlindSpot)
        .where(BlindSpot.user_id == user_id, BlindSpot.status == "open")
        .order_by(BlindSpot.severity.desc())
    )
    return list(q.scalars().all())


def axis_statement(axis: str) -> str:
    return _statement_for(axis)


def preferred_scenarios_for(axis: str) -> list[str]:
    return _AXIS_PREFERRED_SCENARIOS.get(axis, [])


__all__ = [
    "detect_blind_spots",
    "persist_blind_spots",
    "open_blind_spots",
    "axis_statement",
    "preferred_scenarios_for",
    "LOW_N_THRESHOLD",
    "HIGH_VARIANCE_THRESHOLD",
]