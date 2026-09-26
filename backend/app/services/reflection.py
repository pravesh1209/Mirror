"""Self-critique after a prediction miss.

Uses the LLM if available; falls back to a template that names the specific
uncertain axes. Never invents a psychological explanation.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from ..ai.factory import get_provider
from ..ai.prompts import load_prompt
from ..ai.schemas import Reflection

log = logging.getLogger("mirror.services.reflection")


def _template_reflection(
    *,
    predicted_label: str,
    actual_label: str,
    features: dict[str, float | None],
    confidence_parts: dict[str, float],
) -> dict[str, str]:
    missing = sorted([k for k, v in features.items() if v is None])
    failed = (
        f"The model weighted the fit to prior choices too heavily for "
        f"Option {predicted_label}; the actual choice was Option {actual_label}."
    )
    new_evidence = (
        f"New observation: user chose {actual_label} when the model "
        f"expected {predicted_label}."
    )
    if "adaptability" in missing:
        update = (
            "Increase the weight on adaptability once reveal scenarios have "
            "been observed; the model has no adaptability signal yet."
        )
    elif confidence_parts.get("scenario_similarity", 0.0) < 0.4:
        update = (
            "Scenario similarity was low for this case; when the model has "
            "more scenarios close to this one, the choice weights should be "
            "refit on a broader base."
        )
    else:
        update = (
            "Refit the choice weights on the full decision history; the "
            "current weights slightly underestimate the observed preference."
        )
    return {
        "failed_assumption": failed,
        "new_evidence": new_evidence,
        "model_update": update,
    }


async def reflect_on_miss(
    *,
    predicted_label: str,
    actual_label: str,
    features: dict[str, float | None],
    confidence_parts: dict[str, float],
) -> dict[str, str]:
    provider = get_provider()
    if provider.name != "null":
        payload = {
            "predicted_label": predicted_label,
            "actual_label": actual_label,
            "feature_vector": {k: v for k, v in features.items() if v is not None},
            "missing_axes": [k for k, v in features.items() if v is None],
            "confidence_parts": confidence_parts,
        }
        try:
            refl: Reflection | None = await provider.complete_json(
                system=load_prompt("model_reflection"),
                user=json.dumps(payload),
                schema=Reflection,
                timeout_s=15.0,
            )
        except Exception:
            log.exception("LLM reflection failed; falling back to template")
            refl = None
        if refl is not None:
            return {
                "failed_assumption": refl.failed_assumption,
                "new_evidence": refl.new_evidence,
                "model_update": refl.model_update,
            }

    return _template_reflection(
        predicted_label=predicted_label,
        actual_label=actual_label,
        features=features,
        confidence_parts=confidence_parts,
    )


__all__ = ["reflect_on_miss"]