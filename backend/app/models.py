"""SQLAlchemy ORM models for MIRROR.

Portable across SQLite (dev) and PostgreSQL (prod).
JSON columns use the generic JSON type so both backends work.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def uid() -> str:
    return uuid.uuid4().hex


def now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Users & sessions
# ---------------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=uid)
    display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    sessions: Mapped[list["Session"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    decisions: Mapped[list["Decision"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    profiles: Mapped[list["BehaviorProfile"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    predictions: Mapped[list["Prediction"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    mode: Mapped[str] = mapped_column(String(16), default="live")  # live | demo | fallback
    ai_provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="sessions")


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------
class Scenario(Base):
    __tablename__ = "scenarios"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=uid)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    session_id: Mapped[str | None] = mapped_column(ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True)

    domain: Mapped[str] = mapped_column(String(32), default="everyday")
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)

    # scenario attribute vector (0..1)
    difficulty: Mapped[float] = mapped_column(Float, default=0.5)
    risk: Mapped[float] = mapped_column(Float, default=0.5)
    uncertainty: Mapped[float] = mapped_column(Float, default=0.5)
    time_pressure: Mapped[float] = mapped_column(Float, default=0.5)
    novelty: Mapped[float] = mapped_column(Float, default=0.5)
    reward: Mapped[float] = mapped_column(Float, default=0.5)
    information_availability: Mapped[float] = mapped_column(Float, default=0.5)

    time_limit_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    has_reveal: Mapped[bool] = mapped_column(Boolean, default=False)
    reveal_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    source: Mapped[str] = mapped_column(String(16), default="seed")  # seed | llm | fallback
    generator_meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    options: Mapped[list["ScenarioOption"]] = relationship(
        back_populates="scenario", cascade="all, delete-orphan", order_by="ScenarioOption.display_order"
    )


class ScenarioOption(Base):
    __tablename__ = "scenario_options"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=uid)
    scenario_id: Mapped[str] = mapped_column(ForeignKey("scenarios.id", ondelete="CASCADE"), index=True)

    label: Mapped[str] = mapped_column(String(4))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)

    # option attribute vector (0..1)
    risk: Mapped[float] = mapped_column(Float, default=0.5)
    time_cost: Mapped[float] = mapped_column(Float, default=0.5)
    money_cost: Mapped[float] = mapped_column(Float, default=0.5)
    novelty: Mapped[float] = mapped_column(Float, default=0.5)
    uncertainty: Mapped[float] = mapped_column(Float, default=0.5)
    info_availability: Mapped[float] = mapped_column(Float, default=0.5)
    reward: Mapped[float] = mapped_column(Float, default=0.5)
    is_novel: Mapped[bool] = mapped_column(Boolean, default=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    scenario: Mapped[Scenario] = relationship(back_populates="options")


# ---------------------------------------------------------------------------
# Events & decisions
# ---------------------------------------------------------------------------
class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=uid)
    event_id: Mapped[str] = mapped_column(String(40), unique=True, index=True)  # client-provided
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    scenario_id: Mapped[str] = mapped_column(ForeignKey("scenarios.id", ondelete="CASCADE"), index=True)

    event_type: Mapped[str] = mapped_column(String(32))
    option_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    relative_time_ms: Mapped[int] = mapped_column(Integer, default=0)
    client_ts: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    __table_args__ = (
        Index("ix_events_session_scenario_time", "session_id", "scenario_id", "relative_time_ms"),
    )


class Decision(Base):
    __tablename__ = "decisions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=uid)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    scenario_id: Mapped[str] = mapped_column(ForeignKey("scenarios.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    first_option_viewed: Mapped[str | None] = mapped_column(String(4), nullable=True)
    final_option_label: Mapped[str] = mapped_column(String(4))
    final_option_id: Mapped[str | None] = mapped_column(String(32), nullable=True)

    decision_latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    reversal_count: Mapped[int] = mapped_column(Integer, default=0)
    unique_options_viewed: Mapped[int] = mapped_column(Integer, default=0)
    info_items_opened: Mapped[int] = mapped_column(Integer, default=0)

    self_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    reasoning_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    user: Mapped[User] = relationship(back_populates="decisions")

    __table_args__ = (
        UniqueConstraint("session_id", "scenario_id", name="uq_decision_session_scenario"),
    )


# ---------------------------------------------------------------------------
# Behavior features & profiles
# ---------------------------------------------------------------------------
class BehaviorFeature(Base):
    __tablename__ = "behavior_features"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    scenario_id: Mapped[str] = mapped_column(ForeignKey("scenarios.id", ondelete="CASCADE"), index=True)

    feature_vector: Mapped[dict] = mapped_column(JSON, default=dict)
    raw_metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    model_version: Mapped[str] = mapped_column(String(32), default="behavior-v1")
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class BehaviorProfile(Base):
    __tablename__ = "behavior_profiles"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    sample_count: Mapped[int] = mapped_column(Integer, default=0)

    features: Mapped[dict] = mapped_column(JSON, default=dict)
    feature_confidence: Mapped[dict] = mapped_column(JSON, default=dict)
    choice_weights: Mapped[dict] = mapped_column(JSON, default=dict)
    known_patterns: Mapped[list] = mapped_column(JSON, default=list)
    uncertainties: Mapped[list] = mapped_column(JSON, default=list)
    blind_spots: Mapped[list] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    user: Mapped[User] = relationship(back_populates="profiles")

    __table_args__ = (
        UniqueConstraint("user_id", "version", name="uq_profile_user_version"),
    )


# ---------------------------------------------------------------------------
# Predictions
# ---------------------------------------------------------------------------
class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    scenario_id: Mapped[str] = mapped_column(ForeignKey("scenarios.id", ondelete="CASCADE"), index=True)

    profile_version: Mapped[int] = mapped_column(Integer, default=1)

    predicted_first_label: Mapped[str | None] = mapped_column(String(4), nullable=True)
    predicted_final_label: Mapped[str] = mapped_column(String(4))
    predicted_style: Mapped[str] = mapped_column(String(24), default="balanced")

    prob_distribution: Mapped[dict] = mapped_column(JSON, default=dict)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_parts: Mapped[dict] = mapped_column(JSON, default=dict)
    evidence: Mapped[list] = mapped_column(JSON, default=list)
    counterfactuals: Mapped[str | None] = mapped_column(Text, nullable=True)
    narrative: Mapped[str | None] = mapped_column(Text, nullable=True)
    narrative_source: Mapped[str] = mapped_column(String(16), default="template")
    confidence_bands: Mapped[dict] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    user: Mapped[User] = relationship(back_populates="predictions")


class PredictionResult(Base):
    __tablename__ = "prediction_results"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=uid)
    prediction_id: Mapped[str] = mapped_column(
        ForeignKey("predictions.id", ondelete="CASCADE"), unique=True, index=True
    )
    decision_id: Mapped[str] = mapped_column(ForeignKey("decisions.id", ondelete="CASCADE"), index=True)

    choice_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    top2_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    first_action_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    style_correct: Mapped[bool] = mapped_column(Boolean, default=False)

    brier_score: Mapped[float] = mapped_column(Float, default=1.0)
    feature_similarity: Mapped[float] = mapped_column(Float, default=0.0)
    error_analysis: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


# ---------------------------------------------------------------------------
# Blind spots & model updates
# ---------------------------------------------------------------------------
class BlindSpot(Base):
    __tablename__ = "blind_spots"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    axis: Mapped[str] = mapped_column(String(48))
    kind: Mapped[str] = mapped_column(String(32), default="low_n")  # low_n | high_variance | unobserved_condition
    severity: Mapped[float] = mapped_column(Float, default=0.0)
    evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="open")  # open | testing | resolved
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ModelUpdate(Base):
    __tablename__ = "model_updates"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    from_version: Mapped[int] = mapped_column(Integer, default=0)
    to_version: Mapped[int] = mapped_column(Integer, default=1)
    trigger_prediction_id: Mapped[str | None] = mapped_column(
        ForeignKey("predictions.id", ondelete="SET NULL"), nullable=True
    )
    kind: Mapped[str] = mapped_column(String(24), default="initial")  # initial | pattern | correction
    feature_deltas: Mapped[dict] = mapped_column(JSON, default=dict)
    failed_assumption: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    narrative: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
