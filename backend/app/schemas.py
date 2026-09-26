"""Pydantic v2 schemas for MIRROR API."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


# ---------- Errors ----------
class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None
    request_id: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody


# ---------- Sessions ----------
class SessionCreate(BaseModel):
    display_name: str | None = None
    mode: Literal["live", "demo", "fallback"] = "live"


class AIStatus(BaseModel):
    provider: str
    available: bool
    last_error: str | None = None


class SessionResponse(BaseModel):
    session_id: str
    user_id: str
    mode: str
    ai_status: AIStatus


# ---------- Options ----------
class OptionAttributes(BaseModel):
    risk: float = 0.5
    time_cost: float = 0.5
    money_cost: float = 0.5
    novelty: float = 0.5
    uncertainty: float = 0.5
    info_availability: float = 0.5
    reward: float = 0.5


class OptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    label: str
    title: str
    description: str
    attributes: OptionAttributes
    is_novel: bool = False
    display_order: int = 0


class ScenarioAttributes(BaseModel):
    difficulty: float = 0.5
    risk: float = 0.5
    uncertainty: float = 0.5
    time_pressure: float = 0.5
    novelty: float = 0.5
    reward: float = 0.5
    information_availability: float = 0.5


class ScenarioOut(BaseModel):
    id: str
    domain: str
    title: str
    body: str
    attributes: ScenarioAttributes
    time_limit_sec: int | None = None
    has_reveal: bool = False
    reveal_payload: dict | None = None
    source: str
    options: list[OptionOut]


class ScenarioGenerateRequest(BaseModel):
    session_id: str
    domain: str | None = None
    target_axes: list[str] | None = None
    difficulty: float | None = None
    use_bank_only: bool = False


class ScenarioGenerateResponse(BaseModel):
    scenario: ScenarioOut


# ---------- Events ----------
class EventIn(BaseModel):
    event_id: str
    event_type: str
    option_id: str | None = None
    payload: dict[str, Any] | None = None
    relative_time_ms: int = 0
    client_ts: datetime | None = None


class EventsBatchRequest(BaseModel):
    session_id: str
    events: list[EventIn]


class EventsBatchResponse(BaseModel):
    accepted: int
    duplicates_ignored: int


# ---------- Decisions ----------
class DecisionRequest(BaseModel):
    session_id: str
    final_option_id: str
    self_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    reasoning_text: str | None = None


class DecisionDerived(BaseModel):
    decision_latency_ms: int
    first_option_viewed: str | None
    unique_options_viewed: int
    reversal_count: int
    info_items_opened: int


class DecisionResponse(BaseModel):
    decision_id: str
    derived: DecisionDerived
    feature_vector: dict[str, float | None]
    profile_version: int


# ---------- Profile / Fingerprint ----------
class FeatureConfidence(BaseModel):
    level: Literal["HIGH", "MEDIUM", "LOW"]
    score: float
    n: int


class FingerprintResponse(BaseModel):
    user_id: str
    sample_count: int
    version: int
    features: dict[str, float | None]
    confidence: dict[str, FeatureConfidence]
    patterns: list[str]
    insufficient: list[str]


class ProfileStats(BaseModel):
    observations: int
    predictions: int
    resolved: int
    correct: int
    choice_accuracy: float | None
    top2_accuracy: float | None
    mean_brier: float | None
    calibration_available: bool
    calibration_note: str


class ProfileResponse(BaseModel):
    user_id: str
    version: int
    sample_count: int
    features: dict[str, float | None]
    choice_weights: dict[str, float]
    stats: ProfileStats


# ---------- Predictions ----------
class PredictionRequest(BaseModel):
    user_id: str
    scenario_id: str


class PredictedOption(BaseModel):
    label: str
    option_id: str
    probability: float


class PredictionResponse(BaseModel):
    prediction_id: str
    profile_version: int
    predicted_first_option: PredictedOption | None
    predicted_final_option: PredictedOption
    probability_distribution: dict[str, float]
    predicted_style: str
    confidence: float
    confidence_parts: dict[str, float]
    confidence_bands: dict[str, list[str]]
    what_could_change_it: str | None
    evidence: list[str]
    narrative: str | None
    narrative_source: str


class CompareRow(BaseModel):
    facet: str
    predicted: str | None
    actual: str | None
    match: bool | None


class CompareMetrics(BaseModel):
    choice_correct: bool
    top2_correct: bool
    brier_score: float
    feature_similarity: float


class ErrorAnalysis(BaseModel):
    failed_assumption: str | None
    new_evidence: str | None
    model_update: str | None


class ResolveRequest(BaseModel):
    decision_id: str


class ResolveResponse(BaseModel):
    prediction_id: str
    rows: list[CompareRow]
    metrics: CompareMetrics
    error_analysis: ErrorAnalysis | None


# ---------- Blind spots ----------
class BlindSpotAxis(BaseModel):
    axis: str
    statement: str
    n: int
    kind: str | None = None
    severity: float | None = None


class BlindSpotsAnalyzeRequest(BaseModel):
    user_id: str


class BlindSpotsResponse(BaseModel):
    known: list[BlindSpotAxis]
    unknown: list[BlindSpotAxis]


class BlindSpotTestRequest(BaseModel):
    user_id: str
    axis: str


class BlindSpotTestResponse(BaseModel):
    scenario: ScenarioOut


# ---------- Timeline ----------
class TimelineEntry(BaseModel):
    version: int
    at: datetime
    after_decision_n: int
    kind: str
    narrative: str
    deltas: dict[str, float] = Field(default_factory=dict)


class TimelineResponse(BaseModel):
    entries: list[TimelineEntry]


# ---------- What-if ----------
class WhatIfRequest(BaseModel):
    overrides: dict[str, float]


class WhatIfResponse(BaseModel):
    previous_final: str
    new_final: str
    reason: str
    delta_confidence: float


# ---------- Status ----------
class HealthResponse(BaseModel):
    status: str = "ok"
    version: str


class StatusResponse(BaseModel):
    db: str
    ai: AIStatus
    mode: str
