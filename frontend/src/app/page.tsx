"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { LoopAnimation } from "@/components/LoopAnimation";
import { api, MirrorApiError } from "@/lib/api";

const SESSION_KEY = "mirror.session";
const USER_KEY = "mirror.user";

export default function LandingPage() {
  const router = useRouter();
  const [busy, setBusy] = useState<null | "live" | "demo">(null);
  const [error, setError] = useState<string | null>(null);

  async function startLive() {
    setBusy("live");
    setError(null);
    try {
      const sess = await api.createSession({ mode: "live" });
      localStorage.setItem(SESSION_KEY, sess.session_id);
      localStorage.setItem(USER_KEY, sess.user_id);
      router.push("/dashboard");
    } catch (e) {
      setError(
        e instanceof MirrorApiError
          ? `Backend returned ${e.status}: ${e.message}`
          : "Could not reach the MIRROR backend."
      );
      setBusy(null);
    }
  }

  async function loadDemo() {
    setBusy("demo");
    setError(null);
    try {
      const seeded = await api.seedDemo();
      localStorage.setItem(SESSION_KEY, seeded.session_id);
      localStorage.setItem(USER_KEY, seeded.user_id);
      router.push("/dashboard");
    } catch (e) {
      setError(
        e instanceof MirrorApiError
          ? `Backend returned ${e.status}: ${e.message}`
          : "Could not reach the MIRROR backend."
      );
      setBusy(null);
    }
  }

  return (
    <div className="flex flex-col gap-12">
      {/* HERO */}
      <section className="animate-fade-in pt-8 text-center">
        <div className="mx-auto max-w-3xl">
          <p className="font-mono text-[11px] uppercase tracking-[0.3em] text-fg-faint">
            AI Digital Twin of Decision Behavior
          </p>
          <h1 className="mt-6 font-serif text-5xl leading-tight tracking-tight sm:text-6xl">
            MIRROR
          </h1>
          <p className="mt-6 text-xl text-fg-muted">
            Can AI predict your next decision?
          </p>
          <p className="mt-2 text-2xl font-medium text-fg">
            MIRROR learns how you make decisions — not why.
          </p>
          <p className="mx-auto mt-6 max-w-xl text-sm text-fg-muted">
            MIRROR records the decisions you actually make inside short
            scenarios, converts them into deterministic behavioral features,
            and tests whether a small model of you can predict your next
            choice. It does not read thoughts, diagnose personality, or infer
            private mental states.
          </p>

          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Button size="lg" onClick={startLive} loading={busy === "live"}>
              START MY MIRROR
            </Button>
            <Button
              size="lg"
              variant="secondary"
              onClick={loadDemo}
              loading={busy === "demo"}
            >
              LOAD DEMO DATA
            </Button>
          </div>

          {error ? (
            <p className="mt-4 text-xs text-miss" role="alert">
              {error} — start the backend on port 8000 and try again.
            </p>
          ) : null}
        </div>

        <div className="mx-auto mt-14 max-w-3xl rounded-lg border hairline bg-bg-surface/40 px-6 py-5">
          <LoopAnimation />
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section id="how" className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader title="Observe" subtitle="Behavioural telemetry" />
          <CardBody className="text-sm text-fg-muted">
            You complete short scenarios. MIRROR records options viewed, time
            to decide, reversals, information opened, and your final choice.
          </CardBody>
        </Card>
        <Card>
          <CardHeader title="Model" subtitle="Deterministic features" />
          <CardBody className="text-sm text-fg-muted">
            A behavioral engine turns those events into a 9-axis feature
            vector: decision speed, exploration, risk, evidence seeking,
            consistency, adaptability, and more.
          </CardBody>
        </Card>
        <Card>
          <CardHeader title="Predict" subtitle="With confidence" />
          <CardBody className="text-sm text-fg-muted">
            A fitted softmax choice model predicts how you will approach an
            unseen scenario — with an explicit confidence breakdown and the
            evidence behind the prediction.
          </CardBody>
        </Card>
      </section>

      <section className="rounded-lg border hairline bg-bg-surface/40 p-6">
        <h2 className="text-sm font-medium tracking-tight">What MIRROR never does</h2>
        <ul className="mt-3 grid gap-2 text-sm text-fg-muted sm:grid-cols-3">
          <li>• Read your mind</li>
          <li>• Diagnose personality</li>
          <li>• Infer mental health</li>
          <li>• Score your intelligence</li>
          <li>• Collect biometrics</li>
          <li>• Send your data anywhere</li>
        </ul>
      </section>
    </div>
  );
}