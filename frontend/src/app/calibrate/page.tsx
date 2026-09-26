"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { ScenarioPlayer } from "@/features/scenario/ScenarioPlayer";
import { api, MirrorApiError } from "@/lib/api";
import type { DecisionResponse, ScenarioOut } from "@/types/api";

const TARGET_SCENARIOS = 5;

export default function CalibratePage() {
  const router = useRouter();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [scenario, setScenario] = useState<ScenarioOut | null>(null);
  const [completed, setCompleted] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const startedRef = useRef(false);

  useEffect(() => {
    if (startedRef.current) return;
    startedRef.current = true;

    (async () => {
      try {
        let sid = localStorage.getItem("mirror.session");
        if (!sid) {
          const s = await api.createSession({ mode: "live" });
          sid = s.session_id;
          localStorage.setItem("mirror.session", s.session_id);
          localStorage.setItem("mirror.user", s.user_id);
        }
        setSessionId(sid);
        await loadNextScenario(sid);
      } catch (e) {
        setError(
          e instanceof MirrorApiError
            ? `${e.status}: ${e.message}`
            : "Could not reach the MIRROR backend."
        );
        setLoading(false);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadNextScenario = useCallback(async (sid: string) => {
    setLoading(true);
    try {
      const res = await api.generateScenario({
        session_id: sid,
        use_bank_only: false,
      });
      setScenario(res.scenario);
    } catch (e) {
      setError(
        e instanceof MirrorApiError
          ? `${e.status}: ${e.message}`
          : "Scenario generation failed."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  const onDecisionComplete = async (decision: DecisionResponse) => {
    void decision;
    const next = completed + 1;
    setCompleted(next);
    if (next >= TARGET_SCENARIOS) {
      router.push("/fingerprint");
      return;
    }
    if (sessionId) {
      await loadNextScenario(sessionId);
    }
  };

  if (error) {
    return (
      <Card>
        <CardHeader title="Calibration error" />
        <CardBody className="space-y-3 text-sm text-miss">
          <p>{error}</p>
          <Button variant="secondary" onClick={() => location.reload()}>
            Retry
          </Button>
        </CardBody>
      </Card>
    );
  }

  if (loading || !scenario || !sessionId) {
    return (
      <Card>
        <CardBody className="text-sm text-fg-muted">
          Preparing scenario {completed + 1} of {TARGET_SCENARIOS}…
        </CardBody>
      </Card>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      {/* Header: initial calibration context */}
      <Card>
        <CardBody className="space-y-2 text-xs text-fg-muted">
          <div className="flex items-center gap-2">
            <span className="text-[10px] uppercase tracking-widest text-fg-faint">
              Initial calibration
            </span>
            <span className="font-mono text-fg">
              {completed + 1} / {TARGET_SCENARIOS}
            </span>
          </div>
          <p>
            You are completing <strong className="text-fg">5 calibration
            scenarios</strong>. These give MIRROR its first behavioral profile.
            Prediction accuracy is reported later — after{" "}
            <strong className="text-fg">10 resolved predictions</strong> — because
            a smaller number would be statistically meaningless.
          </p>
        </CardBody>
      </Card>

      <div className="flex items-center justify-end gap-1">
        {Array.from({ length: TARGET_SCENARIOS }).map((_, i) => (
          <span
            key={i}
            className={`h-1 w-6 rounded ${
              i < completed
                ? "bg-accent"
                : i === completed
                  ? "bg-fg-muted"
                  : "bg-line/15"
            }`}
          />
        ))}
      </div>

      <ScenarioPlayer
        key={scenario.id}
        sessionId={sessionId}
        scenario={scenario}
        onComplete={onDecisionComplete}
      />
    </div>
  );
}