"""Tests for the LLM JSON repair pipeline."""
from __future__ import annotations

from app.ai.json_repair import extract_json_text, parse_and_validate, parse_json_loose
from app.ai.schemas import PredictionNarrative


def test_plain_json():
    raw = '{"what": "You will explore.", "why": ["a", "b"], "confidence_note": "ok", "what_could_change": "x"}'
    out = parse_and_validate(raw, PredictionNarrative)
    assert out is not None
    assert out.what == "You will explore."


def test_fenced_json():
    raw = '```json\n{"what": "w", "why": ["a"], "confidence_note": "c", "what_could_change": "x"}\n```'
    out = parse_and_validate(raw, PredictionNarrative)
    assert out is not None and out.what == "w"


def test_leading_prose():
    raw = 'Sure, here is the JSON: {"what": "w", "why": ["a"], "confidence_note": "c", "what_could_change": "x"} Done.'
    out = parse_and_validate(raw, PredictionNarrative)
    assert out is not None and out.what == "w"


def test_trailing_comma():
    raw = '{"what": "w", "why": ["a",], "confidence_note": "c", "what_could_change": "x",}'
    out = parse_and_validate(raw, PredictionNarrative)
    assert out is not None and out.what == "w"


def test_smart_quotes():
    raw = '{\u201cwhat\u201d: \u201cw\u201d, \u201cwhy\u201d: [\u201ca\u201d], \u201cconfidence_note\u201d: \u201cc\u201d, \u201cwhat_could_change\u201d: \u201cx\u201d}'
    out = parse_and_validate(raw, PredictionNarrative)
    assert out is not None and out.what == "w"


def test_garbage_returns_none():
    assert parse_and_validate("not json at all", PredictionNarrative) is None
    assert parse_json_loose("") is None
    assert extract_json_text("no braces here") is None


def test_wrong_shape_returns_none():
    # valid JSON, wrong schema
    raw = '{"unexpected": 1, "nested": {"a": 2}}'
    assert parse_and_validate(raw, PredictionNarrative) is None


def test_balanced_brace_with_nested_objects():
    raw = 'prefix {"a": {"b": {"c": 1}}, "d": [1,2,3]} suffix'
    out = parse_json_loose(raw)
    assert out == {"a": {"b": {"c": 1}}, "d": [1, 2, 3]}