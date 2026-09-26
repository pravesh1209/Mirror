"""Turn messy LLM output into a validated Pydantic model.

Order of operations:
  1. strip code fences
  2. find the outermost balanced {...} block
  3. json.loads
  4. if that fails, run a small set of repairs (trailing commas, single
     quotes, unquoted keys, smart quotes, control characters)
  5. validate with Pydantic

Any failure returns None. We never raise to the caller.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

log = logging.getLogger("mirror.ai.json_repair")

T = TypeVar("T", bound=BaseModel)

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)
_SMART_QUOTES = {
    "\u201c": '"',
    "\u201d": '"',
    "\u2018": "'",
    "\u2019": "'",
}


def _strip_fences(text: str) -> str:
    m = _FENCE_RE.search(text)
    return m.group(1) if m else text


def _find_outer_brace_block(text: str) -> str | None:
    """Return the first balanced {...} substring, or None."""
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        ch = text[i]
        if esc:
            esc = False
            continue
        if ch == "\\":
            esc = True
            continue
        if ch == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def _basic_repairs(s: str) -> str:
    """Best-effort fixes for common LLM JSON mistakes."""
    # smart quotes -> straight
    for a, b in _SMART_QUOTES.items():
        s = s.replace(a, b)

    # remove trailing commas before } or ]
    s = re.sub(r",(\s*[}\]])", r"\1", s)

    # remove control characters other than \n \r \t
    s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", s)

    return s


def extract_json_text(raw: str) -> str | None:
    """Return the raw JSON string we believe is present, or None."""
    if not raw:
        return None
    body = _strip_fences(raw)
    block = _find_outer_brace_block(body)
    return block or None


def parse_json_loose(raw: str) -> dict[str, Any] | None:
    """Parse `raw` into a dict, applying repairs on failure. Never raises."""
    if not raw:
        return None

    text = extract_json_text(raw)
    if text is None:
        return None

    # first attempt: clean parse
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass

    # second attempt: repairs
    repaired = _basic_repairs(text)
    try:
        obj = json.loads(repaired)
        if isinstance(obj, dict):
            log.debug("JSON repaired on second attempt")
            return obj
    except json.JSONDecodeError as exc:
        log.debug("JSON still invalid after repair: %s", exc)
        return None

    return None


def parse_and_validate(raw: str, schema: type[T]) -> T | None:
    """Full pipeline: raw text -> validated Pydantic model, or None."""
    data = parse_json_loose(raw)
    if data is None:
        return None
    try:
        return schema.model_validate(data)
    except ValidationError as exc:
        log.debug("JSON parsed but failed schema validation: %s", exc)
        return None


__all__ = [
    "extract_json_text",
    "parse_json_loose",
    "parse_and_validate",
]