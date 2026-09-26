// Typed fetch client for the MIRROR backend.

import type {
  ApiError,
  BlindSpotTestResponse,
  BlindSpotsResponse,
  DecisionRequest,
  DecisionResponse,
  DemoSeedResponse,
  EventsBatchRequest,
  EventsBatchResponse,
  FingerprintResponse,
  PredictionResponse,
  ProfileResponse,
  ProfileStats,
  ResolveResponse,
  ScenarioGenerateResponse,
  ScenarioOut,
  SessionResponse,
  StatusResponse,
  TimelineResponse,
  WhatIfResponse,
} from "@/types/api";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

export class MirrorApiError extends Error {
  code: string;
  status: number;
  details?: Record<string, unknown> | null;
  requestId?: string | null;

  constructor(status: number, body: ApiError | { detail?: string }) {
    const err =
      "error" in body && body.error
        ? body.error
        : { code: "HTTP_ERROR", message: (body as { detail?: string }).detail ?? "Request failed" };
    super(err.message);
    this.name = "MirrorApiError";
    this.status = status;
    this.code = err.code;
    this.details = (err as { details?: Record<string, unknown> | null }).details ?? null;
    this.requestId = (err as { request_id?: string | null }).request_id ?? null;
  }
}

async function request<T>(
  path: string,
  init?: RequestInit & { json?: unknown }
): Promise<T> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...(init?.headers as Record<string, string> | undefined),
  };

  let body: BodyInit | undefined;
  if (init?.json !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(init.json);
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers,
    body,
    cache: "no-store",
  });

  if (res.status === 204) {
    return undefined as T;
  }

  const text = await res.text();
  const data = text ? (JSON.parse(text) as unknown) : undefined;

  if (!res.ok) {
    throw new MirrorApiError(
      res.status,
      (data as ApiError | { detail?: string }) ?? { detail: res.statusText }
    );
  }

  return data as T;
}

export const api = {
  // --- system ---
  health: () => request<{ status: string; version: string }>("/api/health"),
  status: () => request<StatusResponse>("/api/status"),

  // --- sessions ---
  createSession: (body: { display_name?: string; mode?: "live" | "demo" }) =>
    request<SessionResponse>("/api/sessions", { method: "POST", json: body }),
  getSession: (sessionId: string) =>
    request<SessionResponse>(`/api/sessions/${sessionId}`),

  // --- scenarios ---
  generateScenario: (body: {
    session_id: string;
    domain?: string;
    target_axes?: string[];
    difficulty?: number;
    use_bank_only?: boolean;
  }) =>
    request<ScenarioGenerateResponse>("/api/scenarios/generate", {
      method: "POST",
      json: body,
    }),
  getScenario: (scenarioId: string) =>
    request<ScenarioOut>(`/api/scenarios/${scenarioId}`),
  getBank: (domain?: string, limit = 12) =>
    request<{ count: number; scenarios: unknown[] }>(
      `/api/scenarios/bank?limit=${limit}${domain ? `&domain=${domain}` : ""}`
    ),

  // --- events ---
  postEvents: (scenarioId: string, body: EventsBatchRequest) =>
    request<EventsBatchResponse>(`/api/scenarios/${scenarioId}/events`, {
      method: "POST",
      json: body,
    }),

  // --- decisions ---
  submitDecision: (scenarioId: string, body: DecisionRequest) =>
    request<DecisionResponse>(`/api/scenarios/${scenarioId}/decision`, {
      method: "POST",
      json: body,
    }),

  // --- profile ---
  getFingerprint: (userId: string) =>
    request<FingerprintResponse>(`/api/profile/${userId}/fingerprint`),
  getProfile: (userId: string) =>
    request<ProfileResponse>(`/api/profile/${userId}`),
  getStats: (userId: string) =>
    request<ProfileStats>(`/api/profile/${userId}/stats`),
  deleteProfile: (userId: string) =>
    request<void>(`/api/profile/${userId}`, { method: "DELETE" }),

  // --- predictions ---
  createPrediction: (body: { user_id: string; scenario_id: string }) =>
    request<PredictionResponse>("/api/predictions", { method: "POST", json: body }),
  getPrediction: (predictionId: string) =>
    request<PredictionResponse>(`/api/predictions/${predictionId}`),
  resolvePrediction: (predictionId: string, decisionId: string) =>
    request<ResolveResponse>(`/api/predictions/${predictionId}/resolve`, {
      method: "POST",
      json: { decision_id: decisionId },
    }),
  whatIf: (predictionId: string, overrides: Record<string, number>) =>
    request<WhatIfResponse>(`/api/predictions/${predictionId}/whatif`, {
      method: "POST",
      json: { overrides },
    }),

  // --- blind spots ---
  analyzeBlindSpots: (userId: string) =>
    request<BlindSpotsResponse>("/api/blind-spots/analyze", {
      method: "POST",
      json: { user_id: userId },
    }),
  testBlindSpot: (userId: string, axis: string) =>
    request<BlindSpotTestResponse>("/api/blind-spots/test", {
      method: "POST",
      json: { user_id: userId, axis },
    }),

  // --- model ---
  getTimeline: (userId: string) =>
    request<TimelineResponse>(`/api/model/timeline?user_id=${userId}`),

  // --- demo ---
  seedDemo: () => request<DemoSeedResponse>("/api/demo/seed", { method: "POST" }),
  resetDemo: () =>
    request<{ status: string; users_deleted: number }>("/api/demo/reset", {
      method: "POST",
    }),
};

export type Api = typeof api;