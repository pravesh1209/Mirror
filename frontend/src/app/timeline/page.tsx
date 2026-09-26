"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { api, MirrorApiError } from "@/lib/api";
import { FEATURE_LABELS, humanizeFeatureKeys, type FeatureName } from "@/lib/constants";
import { humanDate, num } from "@/lib/format";
import type { TimelineEntry, TimelineResponse } from "@/types/api";

const KIND_TONE = {
  initial: "accent",
  pattern: "hit",
  correction: "miss",
} as const;

export default function Page() {
  const [data, setData] = useState<TimelineResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const uid = localStorage.getItem("mirror.user");
    if (!uid) {
      setLoading(false);
      return;
    }
    (async () => {
      try {
        const res = await api.getTimeline(uid);
        setData(res);
      } catch (e) {
        setError(
          e instanceof MirrorApiError
            ? `${e.status}: ${e.message}`
            : "Backend unreachable."
        );
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <p className="text-sm text-fg-muted">Loading timeline…</p>;

  if (!data || data.entries.length === 0) {
    return (
      <Card>
        <CardHeader
          title="How MIRROR Learned You"
          subtitle={
            error ?? "No model updates yet. Complete a scenario to create the first version."
          }
        />
        <CardBody className="flex gap-2">
          <Link href="/"><Button variant="secondary">Landing</Button></Link>
          <Link href="/calibrate"><Button>Start calibration</Button></Link>
        </CardBody>
      </Card>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-serif text-3xl tracking-tight">How MIRROR Learned You</h1>
        <p className="mt-1 text-sm text-fg-muted">
          Every model version, in order. Deltas show which axes changed.
        </p>
      </div>

      <div className="relative">
        <div className="absolute left-[7px] top-2 bottom-2 w-px bg-line/15" />
        <ol className="space-y-6">
          {data.entries.map((entry) => (
            <TimelineItem key={entry.version} entry={entry} />
          ))}
        </ol>
      </div>
    </div>
  );
}

function TimelineItem({ entry }: { entry: TimelineEntry }) {
  const tone = KIND_TONE[entry.kind as keyof typeof KIND_TONE] ?? "neutral";
  const deltas = Object.entries(entry.deltas);
  const humanNarrative = humanizeFeatureKeys(entry.narrative);

  return (
    <li className="relative pl-8">
      <span className="absolute left-0 top-1.5 h-3.5 w-3.5 rounded-full border border-bg bg-accent" />
      <Card>
        <CardHeader
          title={
            <span className="flex items-center gap-2">
              <span>v{entry.version}</span>
              <Badge tone={tone}>{entry.kind}</Badge>
            </span>
          }
          subtitle={humanDate(entry.at)}
        />
        <CardBody className="space-y-3 text-sm text-fg-muted">
          <p className="text-fg">{humanNarrative}</p>
          {deltas.length > 0 ? (
            <div>
              <div className="text-[11px] uppercase tracking-widest text-fg-faint">Axis deltas</div>
              <div className="mt-2 grid gap-1 sm:grid-cols-2 lg:grid-cols-3">
                {deltas.map(([axis, value]) => (
                  <div
                    key={axis}
                    className="flex items-center justify-between gap-2 rounded border hairline bg-bg/40 px-2 py-1 text-xs"
                  >
                    <span className="text-fg-muted">
                      {FEATURE_LABELS[axis as FeatureName] ?? axis}
                    </span>
                    <span className="font-mono text-fg">{num(value, 2)}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </CardBody>
      </Card>
    </li>
  );
}