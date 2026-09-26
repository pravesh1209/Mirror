"""Prediction vs reality rows and metrics."""
from __future__ import annotations

from dataclasses import dataclass

from ..behavior.scoring import (
    brier_score,
    choice_correct,
    feature_similarity,
    predicted_style,
    top2_correct,
)


@dataclass
class ComparePayload:
    rows: list[dict]
    metrics: dict
    miss: bool


def _actual_style(
    unique_options_viewed: int,
    n_options: int,
    latency_ms: int,
    first_touch_ms: int | None,
) -> str:
    return predicted_style(unique_options_viewed, n_options, latency_ms, first_touch_ms)


def build_compare(
    *,
    predicted_first_label: str | None,
    predicted_final_label: str,
    predicted_style_label: str,
    probability_distribution: dict[str, float],
    actual_first_label: str | None,
    actual_final_label: str,
    actual_style_label: str,
    n_options: int,
    unique_options_viewed: int,
    latency_ms: int,
    first_touch_ms: int | None,
    predicted_profile: dict[str, float | None],
    actual_profile: dict[str, float | None],
) -> ComparePayload:
    rows: list[dict] = []

    # Row: first option
    if predicted_first_label is None and actual_first_label is None:
        rows.append(
            {
                "facet": "First option",
                "predicted": None,
                "actual": None,
                "match": None,
            }
        )
    else:
        rows.append(
            {
                "facet": "First option",
                "predicted": predicted_first_label,
                "actual": actual_first_label,
                "match": predicted_first_label == actual_first_label,
            }
        )

    # Row: top-2 candidates contained the actual choice
    top2 = sorted(
        probability_distribution.items(), key=lambda kv: kv[1], reverse=True
    )[:2]
    top2_labels = [t[0] for t in top2]
    rows.append(
        {
            "facet": "Top-2 candidates",
            "predicted": ", ".join(top2_labels),
            "actual": actual_final_label,
            "match": actual_final_label in top2_labels,
        }
    )

    # Row: final choice
    rows.append(
        {
            "facet": "Final choice",
            "predicted": predicted_final_label,
            "actual": actual_final_label,
            "match": predicted_final_label == actual_final_label,
        }
    )

    # Row: style
    rows.append(
        {
            "facet": "Decision style",
            "predicted": predicted_style_label,
            "actual": actual_style_label,
            "match": predicted_style_label == actual_style_label,
        }
    )

    # --- metrics ---
    choice_ok = choice_correct(probability_distribution, actual_final_label)
    top2_ok = top2_correct(probability_distribution, actual_final_label)
    brier = brier_score(probability_distribution, actual_final_label)
    feat_sim = feature_similarity(predicted_profile, actual_profile)

    metrics = {
        "choice_correct": bool(choice_ok),
        "top2_correct": bool(top2_ok),
        "brier_score": round(float(brier), 4),
        "feature_similarity": round(float(feat_sim), 4),
    }
    return ComparePayload(rows=rows, metrics=metrics, miss=not choice_ok)


__all__ = ["ComparePayload", "build_compare", "_actual_style"]