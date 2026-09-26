"use client";

import { Badge } from "@/components/ui/Badge";
import { axisStatusWord, FEATURE_DESCRIPTIONS, FEATURE_LABELS, type FeatureName } from "@/lib/constants";
import { num } from "@/lib/format";
import type { FeatureConfidence } from "@/types/api";

interface Props {
  name: FeatureName;
  value: number | null;
  confidence: FeatureConfidence;
}

const LEVEL_TONE = { HIGH: "hit", MEDIUM: "warn", LOW: "neutral" } as const;

export function FeatureMeter({ name, value, confidence }: Props) {
  const isNull = value === null || value === undefined;
  const pct = isNull ? 0 : Math.round(value * 100);
  const statusWord = axisStatusWord(confidence.n);

  return (
    <div className="space-y-2">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-sm font-medium tracking-tight">{FEATURE_LABELS[name]}</div>
          <div className="text-[11px] text-fg-faint">{FEATURE_DESCRIPTIONS[name]}</div>
        </div>
        <Badge
          tone={LEVEL_TONE[confidence.level]}
          title={`Evidence level: ${confidence.level} · sample count n=${confidence.n}`}
        >
          {statusWord} · n={confidence.n}
        </Badge>
      </div>

      <div className="flex items-center gap-3">
        <div
          className="relative h-1.5 flex-1 overflow-hidden rounded bg-line/10"
          role="meter"
          aria-valuemin={0}
          aria-valuemax={1}
          aria-valuenow={isNull ? undefined : value}
          aria-valuetext={isNull ? "Not yet observed" : `${pct} percent`}
        >
          {isNull ? (
            <div
              className="h-full w-full"
              style={{
                backgroundImage:
                  "repeating-linear-gradient(90deg, rgb(var(--fg-faint) / 0.35) 0 6px, transparent 6px 12px)",
              }}
            />
          ) : (
            <div className="h-full bg-accent transition-[width] duration-500" style={{ width: `${pct}%` }} />
          )}
        </div>
        <div className="w-14 shrink-0 text-right font-mono text-xs text-fg">
          {isNull ? "—" : num(value, 2)}
        </div>
      </div>

      <div className="text-[11px] text-fg-faint">
        {isNull ? (
          <span>Not yet observed — no scenarios have exercised this axis.</span>
        ) : confidence.n < 6 ? (
          <span>
            Early estimate from {confidence.n}{" "}
            {confidence.n === 1 ? "scenario" : "scenarios"}. Treat as a
            provisional signal, not a stable trait.
          </span>
        ) : (
          <span>Observed across {confidence.n} scenarios.</span>
        )}
      </div>
    </div>
  );
}