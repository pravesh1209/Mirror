"use client";

import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { RadarChart } from "@/components/charts/RadarChart";
import { FeatureMeter } from "@/components/charts/FeatureMeter";
import { FEATURE_NAMES } from "@/lib/constants";
import type { FingerprintResponse } from "@/types/api";

export function FingerprintView({ fp }: { fp: FingerprintResponse }) {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-serif text-3xl tracking-tight">
            Thinking Fingerprint
          </h1>
          <p className="mt-1 text-sm text-fg-muted">
            Observed behavior across {fp.sample_count} completed scenario
            {fp.sample_count === 1 ? "" : "s"}.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge tone="accent">model v{fp.version}</Badge>
          {fp.insufficient.length > 0 ? (
            <Badge tone="warn">
              {fp.insufficient.length} axes not yet observed
            </Badge>
          ) : null}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <Card>
          <CardHeader
            title="Feature radar"
            subtitle="Dots are coloured by per-axis confidence. Axis labels are abbreviations — see the meter list below for full names."
          />
          <CardBody className="flex items-center justify-center px-8 py-8">
            <div className="w-full max-w-[440px]">
              <RadarChart features={fp.features} confidence={fp.confidence} />
            </div>
          </CardBody>
        </Card>

        <div className="flex flex-col gap-4">
          <Card>
            <CardHeader
              title="Observed patterns"
              subtitle={
                fp.patterns.length > 0
                  ? "Statements supported by your recorded decisions."
                  : "No strong patterns detected yet."
              }
            />
            <CardBody className="space-y-2 text-sm text-fg-muted">
              {fp.patterns.length === 0 ? (
                <p>
                  Complete a few more scenarios to reveal patterns. MIRROR does
                  not invent statements it cannot support.
                </p>
              ) : (
                <ul className="space-y-2">
                  {fp.patterns.map((p, i) => (
                    <li key={i} className="flex gap-2">
                      <span className="text-accent">•</span>
                      <span>{p}</span>
                    </li>
                  ))}
                </ul>
              )}
            </CardBody>
          </Card>

          <Card>
            <CardHeader
              title="Not yet observed"
              subtitle="Axes with insufficient evidence."
            />
            <CardBody className="text-sm text-fg-muted">
              {fp.insufficient.length === 0 ? (
                <p>All axes have been exercised at least once.</p>
              ) : (
                <ul className="flex flex-wrap gap-2">
                  {fp.insufficient.map((axis) => (
                    <li key={axis}>
                      <Badge tone="neutral">{axis.replace(/_/g, " ")}</Badge>
                    </li>
                  ))}
                </ul>
              )}
            </CardBody>
          </Card>
        </div>
      </div>

      <Card>
        <CardHeader
          title="Per-axis detail"
          subtitle="Numeric values with confidence bands. Null means not yet observed."
        />
        <CardBody>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURE_NAMES.map((name) => (
              <FeatureMeter
                key={name}
                name={name}
                value={fp.features[name]}
                confidence={
                  fp.confidence[name] ?? { level: "LOW", score: 0, n: 0 }
                }
              />
            ))}
          </div>
        </CardBody>
      </Card>
    </div>
  );
}