"""Pydantic models for LLM structured outputs.

These are separate from app/schemas.py (which is the HTTP DTO layer) so
the AI boundary has its own explicit contract.
"""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class GeneratedOption(BaseModel):
    label: str = Field(min_length=1, max_length=4)
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=800)

    risk: float = Field(ge=0.0, le=1.0)
    time_cost: float = Field(ge=0.0, le=1.0)
    money_cost: float = Field(ge=0.0, le=1.0)
    novelty: float = Field(ge=0.0, le=1.0)
    uncertainty: float = Field(ge=0.0, le=1.0)
    info_availability: float = Field(ge=0.0, le=1.0)
    reward: float = Field(ge=0.0, le=1.0)
    is_novel: bool = False

    @field_validator("label")
    @classmethod
    def _upper_label(cls, v: str) -> str:
        return v.strip().upper()


class GeneratedScenario(BaseModel):
    domain: str = Field(min_length=2, max_length=32)
    title: str = Field(min_length=3, max_length=200)
    body: str = Field(min_length=20, max_length=2000)

    difficulty: float = Field(ge=0.0, le=1.0)
    risk: float = Field(ge=0.0, le=1.0)
    uncertainty: float = Field(ge=0.0, le=1.0)
    time_pressure: float = Field(ge=0.0, le=1.0)
    novelty: float = Field(ge=0.0, le=1.0)
    reward: float = Field(ge=0.0, le=1.0)
    information_availability: float = Field(ge=0.0, le=1.0)

    time_limit_sec: int | None = None
    has_reveal: bool = False
    reveal_payload: dict | None = None

    options: list[GeneratedOption] = Field(min_length=2, max_length=5)

    @field_validator("options")
    @classmethod
    def _labels_unique(cls, v: list[GeneratedOption]) -> list[GeneratedOption]:
        labels = [o.label for o in v]
        if len(set(labels)) != len(labels):
            raise ValueError("option labels must be unique")
        return v


class ValidationVerdict(BaseModel):
    ok: bool
    issues: list[str] = Field(default_factory=list)


class PredictionNarrative(BaseModel):
    what: str
    why: list[str] = Field(default_factory=list)
    confidence_note: str
    what_could_change: str


class BlindSpotChallenge(BaseModel):
    rationale: str
    scenario: GeneratedScenario


class Reflection(BaseModel):
    failed_assumption: str
    new_evidence: str
    model_update: str


__all__ = [
    "GeneratedOption",
    "GeneratedScenario",
    "ValidationVerdict",
    "PredictionNarrative",
    "BlindSpotChallenge",
    "Reflection",
]