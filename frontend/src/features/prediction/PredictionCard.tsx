"use client";

import { Badge } from "@/components/ui/Badge";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { pct } from "@/lib/format";
import type { PredictionResponse, ScenarioOut } from "@/types/api";

interface Props {
  prediction: PredictionResponse;
  scenario: ScenarioOut;
}

export function PredictionCard({ prediction, scenario }: Props) {
  const finalLabel = prediction.predicted_final_option.label;
  const finalOption = scenario.options.find((o) => o.label === finalLabel);
  const firstLabel = prediction.predicted_first_option?.label ?? null;
  const firstOption = firstLabel
    ? scenario.options.find((o) => o.label === firstLabel)
    : null;

  const band =
    prediction.confidence >= 0.7
      ? "HIGH"
      : prediction.confidence >= 0.45
        ? "MEDIUM"
        : "LOW";
  const bandTone = band === "HIGH" ? "hit" : band === "MEDIUM" ? "warn" : "neutral";

  return (
    <Card className="border-accent/30">
      <CardHeader
        title="MIRROR THINKS YOU WILL…"
        subtitle={`Based on model v${prediction.profile_version}`}
        action={<Badge tone={bandTone}>{band} · {pct(prediction.confidence)}</Badge>}
      />
      <CardBody className="space-y-5">
        <div className="grid gap-4 sm:grid-cols-2">
          <Stat
            label="Predicted first action"
            value={
              firstOption
                ? `Option ${firstOption.label} — ${firstOption.title}`
                : "—"
            }
          />
          <Stat
            label="Predicted final choice"
            value={
              finalOption
                ? `Option ${finalOption.label} — ${finalOption.title}`
                : finalLabel
            }
            emphasis
          />
        </div>

        <div>
          <div className="text-[11px] uppercase tracking-widest text-fg-faint">
            Probability distribution
          </div>
          <div className="mt-2 space-y-1.5">
            {scenario.options.map((opt) => {
              const p = prediction.probability_distribution[opt.label] ?? 0;
              const isPredicted = opt.label === finalLabel;
              return (
                <div key={opt.id} className="flex items-center gap-3">
                  <span className="w-6 font-mono text-xs text-fg-muted">
                    {opt.label}
                  </span>
                  <span className="flex-1 text-xs text-fg-muted truncate">
                    {opt.title}
                  </span>
                  <span className="w-24 shrink-0">
                    <span className="block h-1 overflow-hidden rounded bg-line/10">
                      <span
                        className={`block h-full ${
                          isPredicted ? "bg-accent" : "bg-fg-muted/50"
                        }`}
                        style={{ width: `${Math.round(p * 100)}%` }}
                      />
                    </span>
                  </span>
                  <span className="w-10 shrink-0 text-right font-mono text-xs text-fg">
                    {pct(p, 0)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-3">
          <MiniStat
            label="scenario similarity"
            value={pct(prediction.confidence_parts.scenario_similarity ?? 0, 0)}
          />
          <MiniStat
            label="decisiveness"
            value={pct(prediction.confidence_parts.decisiveness ?? 0, 0)}
          />
          <MiniStat
            label="sample support"
            value={pct(prediction.confidence_parts.sample_support ?? 0, 0)}
          />
        </div>
      </CardBody>
    </Card>
  );
}

function Stat({
  label,
  value,
  emphasis,
}: {
  label: string;
  value: string;
  emphasis?: boolean;
}) {
  return (
    <div>
      <div className="text-[11px] uppercase tracking-widest text-fg-faint">
        {label}
      </div>
      <div
        className={`mt-1 text-sm ${emphasis ? "text-fg font-medium" : "text-fg-muted"}`}
      >
        {value}
      </div>
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border hairline bg-bg/40 px-3 py-2">
      <div className="text-[10px] uppercase tracking-widest text-fg-faint">
        {label}
      </div>
      <div className="mt-0.5 font-mono text-sm text-fg">{value}</div>
    </div>
  );
}