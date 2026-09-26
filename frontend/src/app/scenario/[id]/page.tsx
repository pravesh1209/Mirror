"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { ScenarioPlayer } from "@/features/scenario/ScenarioPlayer";
import { api, MirrorApiError } from "@/lib/api";
import type { DecisionResponse, ScenarioOut } from "@/types/api";

export default function ScenarioPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const scenarioId = params?.id ?? null;

  const [sessionId, setSessionId] = useState<string | null>(null);
  const [scenario, setScenario] = useState<ScenarioOut | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const sid = localStorage.getItem("mirror.session");
    if (!sid) {
      router.push("/");
      return;
    }
    setSessionId(sid);
    if (!scenarioId) return;
    (async () => {
      try {
        const sc = await api.getScenario(scenarioId);
        setScenario(sc);
      } catch (e) {
        setError(
          e instanceof MirrorApiError
            ? `${e.status}: ${e.message}`
            : "Could not load scenario."
        );
      }
    })();
  }, [scenarioId, router]);

  if (error) {
    return (
      <Card>
        <CardHeader title="Could not load scenario" />
        <CardBody className="space-y-3 text-sm text-miss">
          <p>{error}</p>
          <Button variant="secondary" onClick={() => router.push("/dashboard")}>
            Back to dashboard
          </Button>
        </CardBody>
      </Card>
    );
  }

  if (!scenario || !sessionId) {
    return (
      <Card>
        <CardBody className="text-sm text-fg-muted">Loading scenario…</CardBody>
      </Card>
    );
  }

  const onComplete = (_decision: DecisionResponse) => {
    // After a standalone scenario, go back to the dashboard.
    router.push("/dashboard");
  };

  return (
    <ScenarioPlayer
      key={scenario.id}
      sessionId={sessionId}
      scenario={scenario}
      onComplete={onComplete}
    />
  );
}