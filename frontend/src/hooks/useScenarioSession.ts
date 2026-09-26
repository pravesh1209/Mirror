"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { useEventRecorder } from "./useEventRecorder";
import type { DecisionResponse, ScenarioOut } from "@/types/api";

export type Phase = "loading" | "playing" | "submitting" | "done" | "error";

interface Params {
  sessionId: string | null;
  scenario: ScenarioOut | null;
  onComplete?: (decision: DecisionResponse) => void;
}

export interface ScenarioSession {
  phase: Phase;
  chosenId: string | null;
  confidence: number;
  infoOpen: boolean;
  revealShown: boolean;
  viewedCount: number;
  errorMessage: string | null;
  pending: number;
  viewOption: (optionId: string) => void;
  openInfo: () => void;
  closeInfo: () => void;
  select: (optionId: string) => void;
  setConfidence: (value: number) => void;
  submit: () => Promise<DecisionResponse | null>;
}

export function useScenarioSession({
  sessionId,
  scenario,
  onComplete,
}: Params): ScenarioSession {
  const scenarioId = scenario?.id ?? null;
  const recorder = useEventRecorder({ sessionId, scenarioId });

  const [phase, setPhase] = useState<Phase>("loading");
  const [chosenId, setChosenId] = useState<string | null>(null);
  const [confidence, setConfidenceState] = useState(0.6);
  const [infoOpen, setInfoOpen] = useState(false);
  const [revealShown, setRevealShown] = useState(false);
  const [viewedCount, setViewedCount] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const viewed = useRef<Set<string>>(new Set());
  const started = useRef(false);

  // Emit scenario_started exactly once per scenario
  useEffect(() => {
    if (!sessionId || !scenario || started.current) return;
    started.current = true;
    recorder.resetClock();
    recorder.emit("scenario_started");
    setPhase("playing");
    // reset local per-scenario state when scenario changes
    setChosenId(null);
    setInfoOpen(false);
    setRevealShown(false);
    setViewedCount(0);
    viewed.current = new Set();
  }, [sessionId, scenario, recorder]);

  const viewOption = useCallback(
    (optionId: string) => {
      if (viewed.current.has(optionId)) {
        recorder.emit("option_revisited", optionId);
        return;
      }
      viewed.current.add(optionId);
      setViewedCount(viewed.current.size);
      recorder.emit("option_viewed", optionId);
    },
    [recorder]
  );

  const openInfo = useCallback(() => {
    if (infoOpen) return;
    setInfoOpen(true);
    const willReveal = Boolean(scenario?.has_reveal) && !revealShown;
    if (willReveal) setRevealShown(true);
    recorder.emit("information_opened", null, {
      info_id: willReveal ? "reveal" : "detail",
      reveal: willReveal,
    });
  }, [infoOpen, revealShown, scenario?.has_reveal, recorder]);

  const closeInfo = useCallback(() => {
    if (!infoOpen) return;
    setInfoOpen(false);
    recorder.emit("information_closed", null, { info_id: "detail" });
  }, [infoOpen, recorder]);

  const select = useCallback(
    (optionId: string) => {
      if (chosenId === null) {
        recorder.emit("option_selected", optionId);
      } else if (chosenId !== optionId) {
        recorder.emit("decision_changed", optionId);
      }
      setChosenId(optionId);
    },
    [chosenId, recorder]
  );

  const setConfidence = useCallback(
    (value: number) => {
      setConfidenceState(value);
      recorder.emit("confidence_changed", null, { value });
    },
    [recorder]
  );

  const submit = useCallback(async (): Promise<DecisionResponse | null> => {
    if (!sessionId || !scenario || !chosenId) return null;
    setPhase("submitting");
    setErrorMessage(null);
    recorder.emit("decision_submitted", chosenId);
    recorder.emit("scenario_completed", null, { final_option_id: chosenId });

    // Drain the buffer before we POST the decision, so the backend has
    // the full event stream when it computes features.
    await recorder.flush();

    try {
      const res = await api.submitDecision(scenario.id, {
        session_id: sessionId,
        final_option_id: chosenId,
        self_confidence: confidence,
      });
      setPhase("done");
      onComplete?.(res);
      return res;
    } catch (err) {
      setPhase("error");
      setErrorMessage(err instanceof Error ? err.message : "Submit failed");
      return null;
    }
  }, [sessionId, scenario, chosenId, confidence, recorder, onComplete]);

  return {
    phase,
    chosenId,
    confidence,
    infoOpen,
    revealShown,
    viewedCount,
    errorMessage,
    pending: recorder.pending,
    viewOption,
    openInfo,
    closeInfo,
    select,
    setConfidence,
    submit,
  };
}