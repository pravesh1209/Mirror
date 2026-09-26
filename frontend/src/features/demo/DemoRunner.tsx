"use client";

import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { api, MirrorApiError } from "@/lib/api";

type Step = {
  id: string;
  label: string;
  hint: string;
};

const STEPS: Step[] = [
  { id: "seed", label: "1. Seed DEMO DATA", hint: "Creates a labeled fictional profile with 9 decisions." },
  { id: "fingerprint", label: "2. Show the Thinking Fingerprint", hint: "9-axis radar built from the demo history." },
  { id: "predict", label: "3. Predict an unseen scenario", hint: "MIRROR commits to a choice before the user does." },
  { id: "play", label: "4. NOW YOU", hint: "The presenter (or a judge) makes the decision themselves." },
  { id: "compare", label: "5. Prediction vs Reality", hint: "Line-by-line comparison with a reflection if wrong." },
  { id: "blindspots", label: "6. Find a blind spot", hint: "MIRROR names what it still does not know." },
];

interface State {
  seed: "idle" | "running" | "done" | "error";
  predictionId: string | null;
  scenarioId: string | null;
  message: string | null;
}

export function DemoRunner() {
  const router = useRouter();
  const [state, setState] = useState<State>({
    seed: "idle",
    predictionId: null,
    scenarioId: null,
    message: null,
  });

  const setMsg = (msg: string | null) => setState((s) => ({ ...s, message: msg }));

  const runSeed = useCallback(async () => {
    setState((s) => ({ ...s, seed: "running", message: null }));
    try {
      const res = await api.seedDemo();
      localStorage.setItem("mirror.session", res.session_id);
      localStorage.setItem("mirror.user", res.user_id);
      localStorage.setItem("mirror.demo", "1"); // <-- flag for global banner
      setState((s) => ({ ...s, seed: "done" }));
      setMsg(
        `DEMO DATA seeded: ${res.decisions} decisions, ${res.predictions} resolved predictions.`
      );
    } catch (e) {
      setState((s) => ({ ...s, seed: "error" }));
      setMsg(
        e instanceof MirrorApiError
          ? `${e.status}: ${e.message}`
          : "Backend unreachable."
      );
    }
  }, []);

  const runPredict = useCallback(async () => {
    const uid = localStorage.getItem("mirror.user");
    const sid = localStorage.getItem("mirror.session");
    if (!uid || !sid) {
      setMsg("Seed the demo first.");
      return;
    }
    setMsg("Preparing prediction…");
    try {
      const gen = await api.generateScenario({
        session_id: sid,
        use_bank_only: true,
      });
      const pred = await api.createPrediction({
        user_id: uid,
        scenario_id: gen.scenario.id,
      });
      setState((s) => ({
        ...s,
        predictionId: pred.prediction_id,
        scenarioId: gen.scenario.id,
      }));
      setMsg("Prediction ready. Proceed to step 4.");
    } catch (e) {
      setMsg(
        e instanceof MirrorApiError
          ? `${e.status}: ${e.message}`
          : "Prediction failed."
      );
    }
  }, []);

  const goFingerprint = () => router.push("/fingerprint");
  const goPredict = () => {
    if (state.scenarioId) router.push(`/predict/${state.scenarioId}`);
    else setMsg("Run step 3 first.");
  };
  const goBlindSpots = () => router.push("/blindspots");

  return (
    <div className="flex flex-col gap-6">
      <Card className="border-accent/30">
        <CardHeader
          title="Hackathon Demo Mode"
          subtitle="Guided 90-second run. All data is labeled DEMO DATA."
          action={<Badge tone="accent">DEMO</Badge>}
        />
        <CardBody className="space-y-4">
          <ol className="space-y-3">
            {STEPS.map((step) => (
              <StepRow key={step.id} step={step} />
            ))}
          </ol>

          <div className="flex flex-wrap gap-2 pt-2">
            <Button onClick={runSeed} loading={state.seed === "running"}>
              {state.seed === "done" ? "Re-seed DEMO DATA" : "Run step 1"}
            </Button>
            <Button
              variant="secondary"
              onClick={goFingerprint}
              disabled={state.seed !== "done"}
            >
              Step 2
            </Button>
            <Button
              variant="secondary"
              onClick={runPredict}
              disabled={state.seed !== "done"}
            >
              Step 3
            </Button>
            <Button
              variant="secondary"
              onClick={goPredict}
              disabled={!state.scenarioId}
            >
              Step 4
            </Button>
            <Button variant="secondary" onClick={goBlindSpots}>
              Step 6
            </Button>
          </div>

          {state.message ? (
            <p className="text-xs text-fg" role="status">
              {state.message}
            </p>
          ) : null}
        </CardBody>
      </Card>
    </div>
  );
}

function StepRow({ step }: { step: Step }) {
  return (
    <li className="flex gap-3 text-sm">
      <span className="mt-0.5 text-accent">→</span>
      <div>
        <div className="text-fg">{step.label}</div>
        <div className="text-xs text-fg-muted">{step.hint}</div>
      </div>
    </li>
  );
}