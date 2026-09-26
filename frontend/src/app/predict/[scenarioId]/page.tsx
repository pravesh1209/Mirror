"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { ScenarioPlayer } from "@/features/scenario/ScenarioPlayer";
import { PredictionCard } from "@/features/prediction/PredictionCard";
import { EvidenceCard } from "@/features/prediction/EvidenceCard";
import { api, MirrorApiError } from "@/lib/api";
import type {
  DecisionResponse,
  PredictionResponse,
  ScenarioOut,
} from "@/types/api";

type Phase = "loading" | "predicted" | "playing" | "resolving" | "error";

export default function Page() {
  const router = useRouter();
  const params = useParams() as { scenarioId: string };
  const scenarioId = params?.scenarioId;

  const [sessionId, setSessionId] = useState<string | null>(null);
  const [scenario, setScenario] = useState<ScenarioOut | null>(null);
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [phase, setPhase] = useState<Phase>("loading");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const sid = localStorage.getItem("mirror.session");
    const uid = localStorage.getItem("mirror.user");
    if (!sid || !uid) {
      router.push("/");
      return;
    }
    if (!scenarioId) return;
    setSessionId(sid);

    (async () => {
      try {
        const sc = await api.getScenario(scenarioId);
        setScenario(sc);
        const p = await api.createPrediction({
          user_id: uid,
          scenario_id: scenarioId,
        });
        setPrediction(p);
        setPhase("predicted");
      } catch (e) {
        setError(
          e instanceof MirrorApiError
            ? `${e.status}: ${e.message}`
            : "Could not prepare prediction."
        );
        setPhase("error");
      }
    })();
  }, [scenarioId, router]);

  async function onDecisionComplete(decision: DecisionResponse) {
    if (!prediction) return;
    setPhase("resolving");
    try {
      const resolved = await api.resolvePrediction(
        prediction.prediction_id,
        decision.decision_id
      );
      sessionStorage.setItem(
        `mirror.compare.${prediction.prediction_id}`,
        JSON.stringify(resolved)
      );
      router.push(`/compare/${prediction.prediction_id}`);
    } catch (e) {
      setError(
        e instanceof MirrorApiError
          ? `${e.status}: ${e.message}`
          : "Could not resolve prediction."
      );
      setPhase("error");
    }
  }

  if (phase === "error") {
    return (
      <Card>
        <CardHeader title="Prediction error" />
        <CardBody className="space-y-3 text-sm text-miss">
          <p>{error}</p>
          <Button variant="secondary" onClick={() => router.push("/dashboard")}>
            Back to dashboard
          </Button>
        </CardBody>
      </Card>
    );
  }

  if (phase === "loading" || !scenario || !prediction) {
    return (
      <Card>
        <CardBody className="text-sm text-fg-muted">
          MIRROR is preparing a prediction…
        </CardBody>
      </Card>
    );
  }

  if (phase === "predicted") {
    return (
      <div className="flex flex-col gap-6">
        <PredictionCard prediction={prediction} scenario={scenario} />
        <EvidenceCard prediction={prediction} />
        <div className="flex justify-end">
          <Button
            size="lg"
            onClick={() => setPhase("playing")}
            aria-label="Proceed to make your own decision"
          >
            NOW YOU →
          </Button>
        </div>
      </div>
    );
  }

  if (phase === "playing" && sessionId) {
    return (
      <ScenarioPlayer
        key={scenario.id}
        sessionId={sessionId}
        scenario={scenario}
        onComplete={onDecisionComplete}
        submitLabel="Submit decision and see MIRROR vs YOU"
      />
    );
  }

  return (
    <Card>
      <CardBody className="text-sm text-fg-muted">
        Resolving your decision against the prediction…
      </CardBody>
    </Card>
  );
}