"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { newEventId, nowMs } from "@/lib/telemetry";
import type { EventIn, EventType } from "@/types/api";

interface Options {
  sessionId: string | null;
  scenarioId: string | null;
  flushIntervalMs?: number;
  flushThreshold?: number;
}

export interface EventRecorder {
  emit: (type: EventType, optionId?: string | null, payload?: Record<string, unknown>) => void;
  flush: () => Promise<void>;
  resetClock: () => void;
  pending: number;
  flushing: boolean;
}

export function useEventRecorder({
  sessionId,
  scenarioId,
  flushIntervalMs = 2000,
  flushThreshold = 10,
}: Options): EventRecorder {
  const buffer = useRef<EventIn[]>([]);
  const startTs = useRef<number | null>(null);
  const [pending, setPending] = useState(0);
  const [flushing, setFlushing] = useState(false);

  const rel = useCallback((): number => {
    if (startTs.current === null) return 0;
    return Math.max(0, Math.round(nowMs() - startTs.current));
  }, []);

  const resetClock = useCallback((): void => {
    startTs.current = nowMs();
  }, []);

  const doFlush = useCallback(async (): Promise<void> => {
    if (!sessionId || !scenarioId) return;
    if (buffer.current.length === 0) return;
    const batch = buffer.current.splice(0, buffer.current.length);
    setPending(buffer.current.length);
    setFlushing(true);
    try {
      await api.postEvents(scenarioId, { session_id: sessionId, events: batch });
    } catch {
      // Put them back at the front so we do not lose them
      buffer.current = [...batch, ...buffer.current];
      setPending(buffer.current.length);
    } finally {
      setFlushing(false);
    }
  }, [sessionId, scenarioId]);

  const emit = useCallback(
    (
      type: EventType,
      optionId: string | null = null,
      payload: Record<string, unknown> = {}
    ): void => {
      if (!sessionId || !scenarioId) return;

      if (type === "scenario_started") {
        // reset clock and force relative_time 0 for this event
        startTs.current = nowMs();
      }

      const ev: EventIn = {
        event_id: newEventId(),
        event_type: type,
        option_id: optionId,
        payload,
        relative_time_ms: type === "scenario_started" ? 0 : rel(),
        client_ts: new Date().toISOString(),
      };
      buffer.current.push(ev);
      setPending(buffer.current.length);

      if (buffer.current.length >= flushThreshold) {
        void doFlush();
      }
    },
    [sessionId, scenarioId, rel, doFlush, flushThreshold]
  );

  // Interval flush
  useEffect(() => {
    const id = setInterval(() => {
      void doFlush();
    }, flushIntervalMs);
    return () => clearInterval(id);
  }, [doFlush, flushIntervalMs]);

  // Beacon on hide / unload
  useEffect(() => {
    if (!sessionId || !scenarioId) return;
    const base =
      (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");
    const url = `${base}/api/scenarios/${scenarioId}/events`;

    const onHide = (): void => {
      if (buffer.current.length === 0) return;
      const batch = buffer.current.splice(0, buffer.current.length);
      setPending(0);
      try {
        const blob = new Blob(
          [JSON.stringify({ session_id: sessionId, events: batch })],
          { type: "application/json" }
        );
        navigator.sendBeacon(url, blob);
      } catch {
        // last-ditch: ignore
      }
    };

    const onVis = (): void => {
      if (document.visibilityState === "hidden") onHide();
    };

    document.addEventListener("visibilitychange", onVis);
    window.addEventListener("pagehide", onHide);
    return () => {
      document.removeEventListener("visibilitychange", onVis);
      window.removeEventListener("pagehide", onHide);
      void doFlush();
    };
  }, [doFlush, sessionId, scenarioId]);

  return { emit, flush: doFlush, resetClock, pending, flushing };
}