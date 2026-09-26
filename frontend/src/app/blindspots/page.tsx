"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { BlindSpotCard } from "@/features/blindspots/BlindSpotCard";
import { api, MirrorApiError } from "@/lib/api";
import type { BlindSpotsResponse } from "@/types/api";

export default function Page() {
  const router = useRouter();
  const [data, setData] = useState<BlindSpotsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState<string | null>(null);

  const load = useCallback(async () => {
    const uid = localStorage.getItem("mirror.user");
    if (!uid) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const res = await api.analyzeBlindSpots(uid);
      setData(res);
      setError(null);
    } catch (e) {
      setError(
        e instanceof MirrorApiError
          ? `${e.status}: ${e.message}`
          : "Backend unreachable."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const testAxis = async (axis: string) => {
    const uid = localStorage.getItem("mirror.user");
    const sid = localStorage.getItem("mirror.session");
    if (!uid || !sid) return;
    setTesting(axis);
    try {
      const res = await api.testBlindSpot(uid, axis);
      // Persist the scenario and route the user into the player
      localStorage.setItem("mirror.blindspot.scenario", res.scenario.id);
      router.push(`/scenario/${res.scenario.id}`);
    } catch (e) {
      setError(
        e instanceof MirrorApiError
          ? `${e.status}: ${e.message}`
          : "Could not generate challenge scenario."
      );
    } finally {
      setTesting(null);
    }
  };

  if (loading) return <p className="text-sm text-fg-muted">Analyzing…</p>;

  if (!data) {
    return (
      <Card>
        <CardHeader
          title="No MIRROR yet"
          subtitle={error ?? "Start a session to analyze blind spots."}
        />
        <CardBody className="flex gap-2">
          <Link href="/">
            <Button variant="secondary">Landing</Button>
          </Link>
          <Link href="/calibrate">
            <Button>Start calibration</Button>
          </Link>
        </CardBody>
      </Card>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-serif text-3xl tracking-tight">Find My Blind Spots</h1>
          <p className="mt-1 text-sm text-fg-muted">
            MIRROR names the axes it knows and the ones it does not. Every
            unknown comes with a challenge you can take.
          </p>
        </div>
        <Button variant="secondary" onClick={load}>
          Re-analyze
        </Button>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader
            title="MIRROR knows"
            subtitle="Axes with enough evidence to speak confidently."
            action={
              <span className="text-xs text-fg-muted">
                {data.known.length} axes
              </span>
            }
          />
          <CardBody className="space-y-3">
            {data.known.length === 0 ? (
              <p className="text-sm text-fg-muted">
                No axis has enough evidence yet.
              </p>
            ) : (
              data.known.map((a) => (
                <BlindSpotCard key={a.axis} variant="known" axis={a} />
              ))
            )}
          </CardBody>
        </Card>

        <Card className="border-warn/30">
          <CardHeader
            title="MIRROR doesn't know"
            subtitle="Axes MIRROR is unsure about. Test one."
            action={
              <span className="text-xs text-fg-muted">
                {data.unknown.length} axes
              </span>
            }
          />
          <CardBody className="space-y-3">
            {data.unknown.length === 0 ? (
              <p className="text-sm text-fg-muted">
                All observed axes are covered.
              </p>
            ) : (
              data.unknown.map((a) => (
                <BlindSpotCard
                  key={a.axis}
                  variant="unknown"
                  axis={a}
                  onTest={testAxis}
                  testing={testing === a.axis}
                />
              ))
            )}
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardBody className="text-xs text-fg-muted">
          MIRROR does not guess. When an axis has fewer than three
          observations — or the observations disagree with each other — it
          marks that axis as a blind spot instead of writing a story about
          you.
        </CardBody>
      </Card>
    </div>
  );
}