"use client";

import { Badge } from "@/components/ui/Badge";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { num, pct } from "@/lib/format";
import type { ResolveResponse } from "@/types/api";

export function MirrorVsYou({ result }: { result: ResolveResponse }) {
  const m = result.metrics;
  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader
          title="MIRROR VS YOU"
          subtitle="Every row compares a prediction against what actually happened."
          action={
            <Badge tone={m.choice_correct ? "hit" : "miss"}>
              {m.choice_correct ? "MIRROR predicted your choice" : "MIRROR missed"}
            </Badge>
          }
        />
        <CardBody>
          <div className="overflow-hidden rounded-md border hairline">
            <table className="w-full text-sm">
              <thead className="bg-bg/40 text-[10px] uppercase tracking-widest text-fg-faint">
                <tr>
                  <th className="px-3 py-2 text-left font-normal">Facet</th>
                  <th className="px-3 py-2 text-left font-normal">MIRROR</th>
                  <th className="px-3 py-2 text-left font-normal">Actual</th>
                  <th className="w-10 px-3 py-2 text-center font-normal"></th>
                </tr>
              </thead>
              <tbody>
                {result.rows.map((r, i) => (
                  <tr key={i} className="border-t hairline">
                    <td className="px-3 py-2 text-fg-muted">{r.facet}</td>
                    <td className="px-3 py-2 font-mono text-fg">
                      {r.predicted ?? "—"}
                    </td>
                    <td className="px-3 py-2 font-mono text-fg">
                      {r.actual ?? "—"}
                    </td>
                    <td className="px-3 py-2 text-center">
                      {r.match === null ? (
                        <span className="text-fg-faint">—</span>
                      ) : r.match ? (
                        <span className="text-hit">✓</span>
                      ) : (
                        <span className="text-miss">✗</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-5 grid gap-3 sm:grid-cols-4">
            <Metric
              label="Choice accuracy"
              value={m.choice_correct ? "1 / 1" : "0 / 1"}
            />
            <Metric
              label="Top-2 hit"
              value={m.top2_correct ? "yes" : "no"}
            />
            <Metric label="Brier score" value={num(m.brier_score, 3)} />
            <Metric
              label="Feature similarity"
              value={pct(m.feature_similarity, 0)}
            />
          </div>
        </CardBody>
      </Card>

      {result.error_analysis ? (
        <Card className="border-miss/30">
          <CardHeader
            title="Model self-critique"
            subtitle="Generated after a wrong prediction."
            action={<Badge tone="miss">reflection</Badge>}
          />
          <CardBody className="space-y-4 text-sm">
            <Field
              label="Failed assumption"
              value={result.error_analysis.failed_assumption}
            />
            <Field
              label="New evidence"
              value={result.error_analysis.new_evidence}
            />
            <Field
              label="Model update"
              value={result.error_analysis.model_update}
            />
          </CardBody>
        </Card>
      ) : (
        <Card>
          <CardBody className="text-sm text-fg-muted">
            MIRROR predicted this outcome. No reflection needed.
          </CardBody>
        </Card>
      )}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border hairline bg-bg/40 px-3 py-2">
      <div className="text-[10px] uppercase tracking-widest text-fg-faint">
        {label}
      </div>
      <div className="mt-0.5 font-mono text-sm text-fg">{value}</div>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string | null }) {
  return (
    <div>
      <div className="text-[11px] uppercase tracking-widest text-fg-faint">
        {label}
      </div>
      <p className="mt-1 text-fg-muted">{value ?? "—"}</p>
    </div>
  );
}