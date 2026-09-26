"use client";

import { FEATURE_LABELS, FEATURE_NAMES, type FeatureName } from "@/lib/constants";
import type { ConfidenceLevel, FeatureConfidence } from "@/types/api";

interface Props {
  features: Record<string, number | null>;
  confidence: Record<string, FeatureConfidence>;
  size?: number;
}

const LEVEL_COLOR: Record<ConfidenceLevel, string> = {
  HIGH: "rgb(var(--signal-hit))",
  MEDIUM: "rgb(var(--signal-warn))",
  LOW: "rgb(var(--fg-faint))",
};

const SHORT_LABELS: Record<FeatureName, string> = {
  decision_speed: "Speed",
  exploration: "Explore",
  risk_tolerance: "Risk",
  evidence_seeking: "Evidence",
  reconsideration: "Revisit",
  consistency: "Consistency",
  novelty_seeking: "Novelty",
  uncertainty_tolerance: "Uncertainty",
  adaptability: "Adapt",
};

export function RadarChart({ features, confidence, size = 400 }: Props) {
  const pad = 90;
  const center = size / 2;
  const radius = center - pad;
  const N = FEATURE_NAMES.length;

  const angles = FEATURE_NAMES.map(
    (_, i) => -Math.PI / 2 + (i * 2 * Math.PI) / N
  );

  function pt(i: number, value: number): [number, number] {
    const a = angles[i];
    const r = value * radius;
    return [center + Math.cos(a) * r, center + Math.sin(a) * r];
  }

  const rings = [0.25, 0.5, 0.75, 1.0];

  const dataPoints: {
    name: FeatureName;
    x: number;
    y: number;
    value: number | null;
  }[] = FEATURE_NAMES.map((name, i) => {
    const v = features[name];
    const [x, y] = pt(i, v === null || v === undefined ? 0 : v);
    return { name, x, y, value: v ?? null };
  });

  const polygonPts = dataPoints
    .filter((p) => p.value !== null)
    .map((p) => `${p.x},${p.y}`)
    .join(" ");

  return (
    <div>
      <svg
        viewBox={`0 0 ${size} ${size}`}
        width="100%"
        height="auto"
        role="img"
        aria-label="Thinking fingerprint radar chart. Full numeric values appear in a table below."
        aria-describedby="radar-table"
        style={{ overflow: "visible" }}
      >
        {rings.map((r) => (
          <polygon
            key={r}
            points={FEATURE_NAMES.map((_, i) => pt(i, r).join(",")).join(" ")}
            fill="none"
            stroke="rgb(var(--line) / 0.08)"
            strokeWidth={1}
          />
        ))}

        {FEATURE_NAMES.map((name, i) => {
          const [x, y] = pt(i, 1);
          return (
            <line
              key={name}
              x1={center}
              y1={center}
              x2={x}
              y2={y}
              stroke="rgb(var(--line) / 0.08)"
              strokeWidth={1}
            />
          );
        })}

        {dataPoints.filter((p) => p.value !== null).length >= 2 ? (
          <polygon
            points={polygonPts}
            fill="rgb(var(--accent) / 0.12)"
            stroke="rgb(var(--accent))"
            strokeWidth={1.5}
            strokeLinejoin="round"
          />
        ) : null}

        {dataPoints.map((p, i) => {
          const c = confidence[p.name];
          const color = c ? LEVEL_COLOR[c.level] : "rgb(var(--fg-faint))";
          if (p.value === null) {
            const [cx, cy] = pt(i, 0.02);
            return (
              <g key={p.name}>
                <circle
                  cx={cx}
                  cy={cy}
                  r={3}
                  fill="none"
                  stroke="rgb(var(--fg-faint))"
                />
                <text
                  x={cx}
                  y={cy + 3}
                  textAnchor="middle"
                  fontSize={7}
                  fill="rgb(var(--fg-faint))"
                >
                  ×
                </text>
              </g>
            );
          }
          return (
            <circle
              key={p.name}
              cx={p.x}
              cy={p.y}
              r={3.5}
              fill={color}
              stroke="rgb(var(--bg))"
              strokeWidth={1}
            />
          );
        })}

        {FEATURE_NAMES.map((name, i) => {
          const a = angles[i];
          const cos = Math.cos(a);
          const sin = Math.sin(a);
          const lx = center + cos * (radius + 14);
          const ly = center + sin * (radius + 14);
          const anchor =
            Math.abs(cos) < 0.3 ? "middle" : cos > 0 ? "start" : "end";
          const dy = Math.abs(cos) < 0.3 ? (sin > 0 ? 10 : -4) : sin > 0 ? 8 : -2;
          const v = features[name];
          return (
            <text
              key={name}
              x={lx}
              y={ly + dy}
              textAnchor={anchor}
              fontSize={10}
              fill="rgb(var(--fg-muted))"
              style={{ letterSpacing: "0.02em" }}
            >
              {SHORT_LABELS[name]}
              {v === null ? " · n/a" : ""}
            </text>
          );
        })}
      </svg>

      {/* Screen-reader-only numeric table */}
      <table
        id="radar-table"
        className="sr-only"
        aria-label="Fingerprint values as a table"
      >
        <caption>Thinking fingerprint values</caption>
        <thead>
          <tr>
            <th scope="col">Axis</th>
            <th scope="col">Value</th>
            <th scope="col">Confidence</th>
            <th scope="col">Sample count</th>
          </tr>
        </thead>
        <tbody>
          {FEATURE_NAMES.map((name) => {
            const v = features[name];
            const c = confidence[name];
            return (
              <tr key={name}>
                <th scope="row">{FEATURE_LABELS[name]}</th>
                <td>{v === null || v === undefined ? "Not observed" : v.toFixed(2)}</td>
                <td>{c?.level ?? "—"}</td>
                <td>{c?.n ?? 0}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}