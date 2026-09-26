"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { api, MirrorApiError } from "@/lib/api";
import { pct, num, int } from "@/lib/format";
import type {
  BlindSpotsResponse,
  FingerprintResponse,
  ProfileStats,
} from "@/types/api";

type BlindSpotFetch = "loading" | "loaded" | "failed";

export default function DashboardPage() {
  const [userId, setUserId] = useState<string | null>(null);
  const [fingerprint, setFingerprint] = useState<FingerprintResponse | null>(null);
  const [stats, setStats] = useState<ProfileStats | null>(null);
  const [blindSpots, setBlindSpots] = useState<BlindSpotsResponse | null>(null);
  const [blindSpotFetch, setBlindSpotFetch] = useState<BlindSpotFetch>("loading");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const uid = localStorage.getItem("mirror.user");
    setUserId(uid);
    if (!uid) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const [fp, st] = await Promise.all([
          api.getFingerprint(uid),
          api.getStats(uid),
        ]);
        if (cancelled) return;
        setFingerprint(fp);
        setStats(st);
      } catch (e) {
        if (cancelled) return;
        setError(
          e instanceof MirrorApiError
            ? `${e.status}: ${e.message}`
            : "Could not reach the backend."
        );
        setBlindSpotFetch("failed");
        setLoading(false);
        return;
      }
      try {
        const bs = await api.analyzeBlindSpots(uid);
        if (!cancelled) {
          setBlindSpots(bs);
          setBlindSpotFetch("loaded");
        }
      } catch {
        if (!cancelled) setBlindSpotFetch("failed");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) return <div className="text-sm text-fg-muted">Loading…</div>;

  if (!userId) {
    return (
      <Card>
        <CardHeader
          title="No active MIRROR"
          subtitle="Start one from the landing page to see your dashboard."
        />
        <CardBody className="flex flex-wrap gap-2">
          <Link href="/">
            <Button>Go to landing page</Button>
          </Link>
          <Link href="/demo">
            <Button variant="secondary">Load demo data</Button>
          </Link>
        </CardBody>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader title="Backend error" />
        <CardBody className="text-sm text-miss" role="alert">
          {error}
        </CardBody>
      </Card>
    );
  }

  const isDemo = localStorage.getItem("mirror.demo") === "1";
  const observedPatterns = fingerprint?.patterns.length ?? 0;
  const unobservedAxes = fingerprint?.insufficient.length ?? 0;
  const detectedBlindSpots = blindSpots?.unknown.length ?? 0;
  const meanConfidence =
    fingerprint && Object.keys(fingerprint.confidence).length > 0
      ? Object.values(fingerprint.confidence).reduce((a, c) => a + c.score, 0) /
        Object.values(fingerprint.confidence).length
      : null;
  const modelConfidenceLabel =
    meanConfidence === null
      ? "—"
      : meanConfidence >= 0.66
        ? "High"
        : meanConfidence >= 0.33
          ? "Medium"
          : "Low";

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-serif text-3xl tracking-tight">MIRROR STATUS</h1>
          <p className="mt-1 text-sm text-fg-muted">
            All numbers computed from stored data. No metrics are invented.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {isDemo ? <Badge tone="accent">DEMO DATA</Badge> : null}
          <Badge tone="accent">v{fingerprint?.version ?? "—"}</Badge>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat title="Observations" value={int(stats?.observations)} hint="scenarios completed" />
        <Stat title="Predictions" value={int(stats?.predictions)} hint="made so far" />
        <Stat title="Resolved" value={int(stats?.resolved)} hint={`of ${int(stats?.predictions)} predictions`} />
        <Stat
          title="Prediction accuracy"
          value={
            stats?.calibration_available && stats?.choice_accuracy != null
              ? pct(stats.choice_accuracy)
              : "—"
          }
          hint={
            stats?.calibration_available
              ? `correct ${int(stats.correct)} of ${int(stats.resolved)}`
              : stats?.calibration_note ?? "insufficient resolved predictions"
          }
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Stat
          title="Model confidence"
          value={modelConfidenceLabel}
          hint={meanConfidence !== null ? `mean ${num(meanConfidence, 2)} across 9 axes` : "no profile yet"}
        />
        <Stat title="Observed patterns" value={int(observedPatterns)} hint="features with measurable evidence" />
        <Stat title="Unobserved axes" value={int(unobservedAxes)} hint="axes without enough evidence" />
      </div>

      <BlindSpotSummary state={blindSpotFetch} data={blindSpots} unobservedAxes={unobservedAxes} />

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader title="Continue" subtitle="Every MIRROR screen is one click away." />
          <CardBody className="flex flex-wrap gap-2">
            <Link href="/calibrate"><Button>Calibrate</Button></Link>
            <Link href="/fingerprint"><Button variant="secondary">Fingerprint</Button></Link>
            <Link href="/blindspots"><Button variant="secondary">Blind spots</Button></Link>
            <Link href="/timeline"><Button variant="secondary">Timeline</Button></Link>
            <Link href="/demo"><Button variant="secondary">Demo</Button></Link>
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Session" subtitle="Stored locally, in your browser" />
          <CardBody className="space-y-1 text-xs text-fg-muted">
            <div>user_id: <span className="font-mono">{userId}</span></div>
            {fingerprint ? (
              <div>sample count: <span className="font-mono">{fingerprint.sample_count}</span></div>
            ) : null}
            <div className="pt-2">
              <Link href="/settings" className="text-miss hover:underline">Delete my MIRROR</Link>
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}

function BlindSpotSummary({
  state,
  data,
  unobservedAxes,
}: {
  state: BlindSpotFetch;
  data: BlindSpotsResponse | null;
  unobservedAxes: number;
}) {
  const count = data?.unknown.length ?? 0;

  return (
    <Card className={count > 0 ? "border-warn/30" : undefined}>
      <CardHeader
        title="Detected blind spots"
        subtitle="Axes where evidence is weak, contradictory, or absent."
        action={
          count > 0 ? (
            <Link href="/blindspots">
              <Button size="sm" variant="secondary">Open blind spots</Button>
            </Link>
          ) : null
        }
      />
      <CardBody className="space-y-3 text-sm text-fg-muted">
        {state === "loading" ? (
          <p>Analyzing…</p>
        ) : state === "failed" ? (
          <p className="text-miss">Could not analyze blind spots. The backend may be unavailable.</p>
        ) : count === 0 && unobservedAxes === 0 ? (
          <p>No blind spots detected. Every observed axis has enough evidence.</p>
        ) : count === 0 && unobservedAxes > 0 ? (
          <p>
            {unobservedAxes} axes have no observations yet, but none currently
            meet MIRROR&apos;s blind-spot criteria (low sample count, high
            variance, or unobserved condition).
          </p>
        ) : data ? (
          <ul className="space-y-2">
            {data.unknown.slice(0, 3).map((bs) => (
              <li key={bs.axis} className="flex items-start gap-2">
                <span className="mt-1 text-warn">?</span>
                <div>
                  <div className="text-fg">{humanizeAxis(bs.axis)}</div>
                  <div className="text-xs text-fg-faint">
                    {bs.kind === "low_n" && "insufficient samples"}
                    {bs.kind === "high_variance" && "observations disagree"}
                    {bs.kind === "unobserved_condition" && "condition never tested"}
                    {bs.severity != null && ` · evidence gap ${Math.round(bs.severity * 100)}%`}
                  </div>
                </div>
              </li>
            ))}
            {data.unknown.length > 3 ? (
              <li className="text-xs text-fg-faint">and {data.unknown.length - 3} more</li>
            ) : null}
          </ul>
        ) : null}
      </CardBody>
    </Card>
  );
}

function Stat({ title, value, hint }: { title: string; value: string; hint?: string }) {
  return (
    <Card>
      <CardBody className="space-y-1">
        <div className="text-[11px] uppercase tracking-widest text-fg-faint">{title}</div>
        <div className="font-mono text-2xl tracking-tight">{value}</div>
        {hint ? <div className="text-xs text-fg-muted">{hint}</div> : null}
      </CardBody>
    </Card>
  );
}

function humanizeAxis(axis: string): string {
  return axis.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}