// Mirrors the backend Pydantic schemas.

export type SessionMode = "live" | "demo" | "fallback";

export interface AIStatus {
  provider: string;
  available: boolean;
  last_error: string | null;
}

export interface SessionResponse {
  session_id: string;
  user_id: string;
  mode: SessionMode;
  ai_status: AIStatus;
}

export interface StatusResponse {
  db: string;
  ai: AIStatus;
  mode: string;
}

export interface OptionAttributes {
  risk: number;
  time_cost: number;
  money_cost: number;
  novelty: number;
  uncertainty: number;
  info_availability: number;
  reward: number;
}

export interface ScenarioAttributes {
  difficulty: number;
  risk: number;
  uncertainty: number;
  time_pressure: number;
  novelty: number;
  reward: number;
  information_availability: number;
}

export interface OptionOut {
  id: string;
  label: string;
  title: string;
  description: string;
  attributes: OptionAttributes;
  is_novel: boolean;
  display_order: number;
}

export interface ScenarioOut {
  id: string;
  domain: string;
  title: string;
  body: string;
  attributes: ScenarioAttributes;
  time_limit_sec: number | null;
  has_reveal: boolean;
  reveal_payload: { info?: string } | null;
  source: "seed" | "llm" | "fallback";
  options: OptionOut[];
}

export interface ScenarioGenerateResponse {
  scenario: ScenarioOut;
}

export type EventType =
  | "scenario_started"
  | "option_viewed"
  | "option_selected"
  | "information_opened"
  | "information_closed"
  | "option_revisited"
  | "decision_changed"
  | "confidence_changed"
  | "hint_requested"
  | "reasoning_submitted"
  | "decision_submitted"
  | "scenario_completed";

export interface EventIn {
  event_id: string;
  event_type: EventType;
  option_id?: string | null;
  payload?: Record<string, unknown>;
  relative_time_ms: number;
  client_ts?: string | null;
}

export interface EventsBatchRequest {
  session_id: string;
  events: EventIn[];
}

export interface EventsBatchResponse {
  accepted: number;
  duplicates_ignored: number;
}

export interface DecisionRequest {
  session_id: string;
  final_option_id: string;
  self_confidence?: number | null;
  reasoning_text?: string | null;
}

export interface DecisionDerived {
  decision_latency_ms: number;
  first_option_viewed: string | null;
  unique_options_viewed: number;
  reversal_count: number;
  info_items_opened: number;
}

export interface DecisionResponse {
  decision_id: string;
  derived: DecisionDerived;
  feature_vector: Record<string, number | null>;
  profile_version: number;
}

export type ConfidenceLevel = "HIGH" | "MEDIUM" | "LOW";

export interface FeatureConfidence {
  level: ConfidenceLevel;
  score: number;
  n: number;
}

export interface FingerprintResponse {
  user_id: string;
  sample_count: number;
  version: number;
  features: Record<string, number | null>;
  confidence: Record<string, FeatureConfidence>;
  patterns: string[];
  insufficient: string[];
}

export interface ProfileStats {
  observations: number;
  predictions: number;
  resolved: number;
  correct: number;
  choice_accuracy: number | null;
  top2_accuracy: number | null;
  mean_brier: number | null;
  calibration_available: boolean;
  calibration_note: string;
}

export interface ProfileResponse {
  user_id: string;
  version: number;
  sample_count: number;
  features: Record<string, number | null>;
  choice_weights: Record<string, number>;
  stats: ProfileStats;
}

export interface PredictedOption {
  label: string;
  option_id: string;
  probability: number;
}

export interface PredictionResponse {
  prediction_id: string;
  profile_version: number;
  predicted_first_option: PredictedOption | null;
  predicted_final_option: PredictedOption;
  probability_distribution: Record<string, number>;
  predicted_style: string;
  confidence: number;
  confidence_parts: Record<string, number>;
  confidence_bands: { high: string[]; medium: string[]; low: string[] };
  what_could_change_it: string | null;
  evidence: string[];
  narrative: string | null;
  narrative_source: "llm" | "template";
}

export interface CompareRow {
  facet: string;
  predicted: string | null;
  actual: string | null;
  match: boolean | null;
}

export interface CompareMetrics {
  choice_correct: boolean;
  top2_correct: boolean;
  brier_score: number;
  feature_similarity: number;
}

export interface ErrorAnalysis {
  failed_assumption: string | null;
  new_evidence: string | null;
  model_update: string | null;
}

export interface ResolveResponse {
  prediction_id: string;
  rows: CompareRow[];
  metrics: CompareMetrics;
  error_analysis: ErrorAnalysis | null;
}

export interface BlindSpotAxis {
  axis: string;
  statement: string;
  n: number;
  kind?: string | null;
  severity?: number | null;
}

export interface BlindSpotsResponse {
  known: BlindSpotAxis[];
  unknown: BlindSpotAxis[];
}

export interface BlindSpotTestResponse {
  scenario: ScenarioOut;
}

export interface TimelineEntry {
  version: number;
  at: string;
  after_decision_n: number;
  kind: string;
  narrative: string;
  deltas: Record<string, number>;
}

export interface TimelineResponse {
  entries: TimelineEntry[];
}

export interface WhatIfResponse {
  previous_final: string;
  new_final: string;
  reason: string;
  delta_confidence: number;
}

export interface DemoSeedResponse {
  status: string;
  label: string;
  user_id: string;
  session_id: string;
  decisions: number;
  predictions: number;
  ai_status: AIStatus;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown> | null;
    request_id?: string | null;
  };
}