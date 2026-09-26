"""Narrative generation for a prediction.

Primary path: LLM (DeepSeek) with a numeric-consistency check that rejects
the output if the model invents any number not in our allowed set.

Fallback path: a deterministic template. Never fails.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from ..ai.factory import get_provider
from ..ai.prompts import load_prompt
from ..ai.schemas import PredictionNarrative
from .confidence import band_for
from .engine import PredictionComputation

log = logging.getLogger("mirror.prediction.explain")

_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")


def _extract_numbers(text: str) -> set[int]:
    out: set[int] = set()
    for token in _NUMBER_RE.findall(text):
        try:
            out.add(int(float(token)))
        except (TypeError, ValueError):
            continue
    return out


def _template_narrative(
    comp: PredictionComputation,
    final_label: str,
    final_title: str,
) -> str:
    band = band_for(comp.confidence)
    first_part = (
        f"MIRROR expects you to lean toward Option {final_label} — {final_title}."
    )
    evidence_part = " ".join(comp.evidence[:2]) if comp.evidence else ""
    conf_part = (
        f"Confidence: {int(comp.confidence * 100)}% ({band}). "
        f"{comp.counterfactuals}"
    )
    return " ".join(p for p in (first_part, evidence_part, conf_part) if p).strip()


async def _try_llm(
    comp: PredictionComputation,
    final_label: str,
    final_title: str,
) -> str | None:
    provider = get_provider()
    if provider.name == "null":
        return None

    payload: dict[str, Any] = {
        "predicted_final_label": final_label,
        "predicted_final_title": final_title,
        "predicted_first_label": comp.predicted_first_label,
        "predicted_style": comp.predicted_style,
        "confidence_percent": int(comp.confidence * 100),
        "confidence_band": band_for(comp.confidence),
        "probability_distribution_percent": {
            k: int(v * 100) for k, v in comp.probability_distribution.items()
        },
        "evidence": comp.evidence,
        "counterfactual": comp.counterfactuals,
        "allowed_numbers": sorted(comp.allowed_numbers),
    }

    try:
        nar = await provider.complete_json(
            system=load_prompt("prediction_explainer"),
            user=json.dumps(payload),
            schema=PredictionNarrative,
            timeout_s=15.0,
        )
    except Exception:
        log.exception("LLM narrative generation failed")
        return None

    if nar is None:
        return None

    combined = " ".join(
        [nar.what, " ".join(nar.why), nar.confidence_note, nar.what_could_change]
    )
    nums = _extract_numbers(combined)
    unexpected = nums - comp.allowed_numbers
    if unexpected:
        log.warning(
            "LLM narrative contained unexpected numbers %s; falling back to template",
            sorted(unexpected),
        )
        return None

    lines = [nar.what]
    if nar.why:
        lines.append("")
        lines.extend(f"• {w}" for w in nar.why)
    lines.append("")
    lines.append(nar.confidence_note)
    lines.append("")
    lines.append(nar.what_could_change)
    return "\n".join(lines).strip()


async def build_narrative(
    comp: PredictionComputation,
    *,
    final_label: str,
    final_title: str,
) -> tuple[str, str]:
    """Return (narrative, source) where source is 'llm' or 'template'."""
    text = await _try_llm(comp, final_label, final_title)
    if text:
        return text, "llm"
    return _template_narrative(comp, final_label, final_title), "template"


__all__ = ["build_narrative"]