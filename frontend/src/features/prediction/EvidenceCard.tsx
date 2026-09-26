"use client";

import { useMemo } from "react";
import { Badge } from "@/components/ui/Badge";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { checkCopy } from "@/lib/safetyCopy";
import type { PredictionResponse } from "@/types/api";

export function EvidenceCard({ prediction }: { prediction: PredictionResponse }) {
  const bands = prediction.confidence_bands;

  const safeNarrative = useMemo(() => {
    if (!prediction.narrative) return null;
    const check = checkCopy(prediction.narrative);
    if (!check.ok) {
      return {
        text: prediction.narrative,
        unsafe: true,
        reasons: check.violations.map((v) => v.reason),
      };
    }
    return { text: prediction.narrative, unsafe: false, reasons: [] };
  }, [prediction.narrative]);

  return (
    <Card>
      <CardHeader
        title="Why MIRROR predicts this"
        subtitle={
          prediction.narrative_source === "llm"
            ? "Narrated by the AI layer, constrained to computed numbers."
            : "Narrated by the deterministic fallback (no AI available)."
        }
        action={
          <Badge tone={prediction.narrative_source === "llm" ? "accent" : "neutral"}>
            {prediction.narrative_source}
          </Badge>
        }
      />
      <CardBody className="space-y-5">
        {prediction.evidence.length > 0 ? (
          <div>
            <div className="text-[11px] uppercase tracking-widest text-fg-faint">
              Observed evidence
            </div>
            <ul className="mt-2 space-y-2 text-sm text-fg-muted">
              {prediction.evidence.map((e, i) => (
                <li key={i} className="flex gap-2">
                  <span className="text-accent">•</span>
                  <span>{e}</span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        <div>
          <div className="text-[11px] uppercase tracking-widest text-fg-faint">
            Confidence by band
          </div>
          <div className="mt-2 space-y-3 text-sm">
            {bands.high.length > 0 ? (
              <Band tone="hit" label="High">
                {bands.high}
              </Band>
            ) : null}
            {bands.medium.length > 0 ? (
              <Band tone="warn" label="Medium">
                {bands.medium}
              </Band>
            ) : null}
            {bands.low.length > 0 ? (
              <Band tone="neutral" label="Low">
                {bands.low}
              </Band>
            ) : null}
          </div>
        </div>

        {prediction.what_could_change_it ? (
          <div className="rounded-md border border-warn/30 bg-warn/5 p-3">
            <div className="text-[10px] uppercase tracking-widest text-warn">
              What could change this prediction
            </div>
            <p className="mt-1 text-sm text-fg">
              {prediction.what_could_change_it}
            </p>
          </div>
        ) : null}

        {safeNarrative ? (
          <div>
            <div className="text-[11px] uppercase tracking-widest text-fg-faint">
              Model narrative
            </div>
            {safeNarrative.unsafe ? (
              <div className="mt-2 rounded-md border border-miss/30 bg-miss/5 p-3 text-sm text-fg">
                <div className="text-[10px] uppercase tracking-widest text-miss">
                  Narrative withheld
                </div>
                <p className="mt-1 text-fg-muted">
                  The generated narrative contained language outside MIRROR&apos;s
                  evidence policy ({safeNarrative.reasons.join(", ")}). It has
                  been hidden rather than displayed.
                </p>
              </div>
            ) : (
              <pre className="mt-2 whitespace-pre-wrap font-sans text-sm text-fg-muted">
                {safeNarrative.text}
              </pre>
            )}
          </div>
        ) : null}
      </CardBody>
    </Card>
  );
}

function Band({
  tone,
  label,
  children,
}: {
  tone: "hit" | "warn" | "neutral";
  label: string;
  children: React.ReactNode;
}) {
  const toneClass =
    tone === "hit"
      ? "text-hit border-hit/30"
      : tone === "warn"
        ? "text-warn border-warn/30"
        : "text-fg-muted border hairline";
  return (
    <div>
      <span
        className={`inline-flex items-center gap-1 rounded border px-2 py-0.5 text-[10px] uppercase tracking-widest ${toneClass}`}
      >
        {label}
      </span>
      <ul className="mt-1.5 space-y-1 text-fg-muted">
        {Array.isArray(children)
          ? (children as string[]).map((c, i) => (
              <li key={i} className="flex gap-2">
                <span className="text-fg-faint">–</span>
                <span>{c}</span>
              </li>
            ))
          : null}
      </ul>
    </div>
  );
}