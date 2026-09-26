// Client-side telemetry helpers.

import type { EventType } from "@/types/api";

export const ALL_EVENT_TYPES: readonly EventType[] = [
  "scenario_started",
  "option_viewed",
  "option_selected",
  "information_opened",
  "information_closed",
  "option_revisited",
  "decision_changed",
  "confidence_changed",
  "hint_requested",
  "reasoning_submitted",
  "decision_submitted",
  "scenario_completed",
] as const;

export function newEventId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  // fallback for ancient browsers
  return `evt_${Math.random().toString(36).slice(2)}_${Date.now()}`;
}

export function nowMs(): number {
  if (typeof performance !== "undefined" && "now" in performance) {
    return performance.now();
  }
  return Date.now();
}