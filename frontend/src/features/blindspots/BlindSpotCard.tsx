"use client";

import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { FEATURE_LABELS, type FeatureName } from "@/lib/constants";
import { pct } from "@/lib/format";
import type { BlindSpotAxis } from "@/types/api";

interface Props {
  variant: "known" | "unknown";
  axis: BlindSpotAxis;
  onTest?: (axis: string) => void;
  testing?: boolean;
}

function displayLabel(axis: string): string {
  return FEATURE_LABELS[axis as FeatureName] ?? axis.replace(/_/g, " ");
}

function kindDescription(kind?: string | null): string {
  switch (kind) {
    case "low_n": return "insufficient samples";
    case "high_variance": return "observations disagree";
    case "unobserved_condition": return "condition never tested";
    default: return "";
  }
}

export function BlindSpotCard({ variant, axis, onTest, testing }: Props) {
  const isUnknown = variant === "unknown";
  const label = displayLabel(axis.axis);

  return (
    <Card className={isUnknown ? "border-warn/30" : undefined}>
      <CardHeader
        title={
          <span className="flex items-center gap-2">
            <span className={isUnknown ? "text-warn" : "text-hit"}>
              {isUnknown ? "?" : "\u2713"}
            </span>
            <span>{label}</span>
          </span>
        }
        action={
          isUnknown && axis.severity != null ? (
            <Badge
              tone="warn"
              title="Evidence gap: how much MIRROR does not yet know about this axis. 100% = no observations; 0% = full coverage."
            >
              evidence gap {pct(axis.severity, 0)}
            </Badge>
          ) : (
            <Badge tone="hit">observed</Badge>
          )
        }
      />
      <CardBody className="space-y-3 text-sm text-fg-muted">
        <p>{axis.statement}</p>
        <div className="flex items-center justify-between gap-2">
          <div className="text-[11px] text-fg-faint">
            {axis.n > 0 ? `${axis.n} observation${axis.n === 1 ? "" : "s"}` : "no observations"}
            {axis.kind ? ` · ${kindDescription(axis.kind)}` : ""}
          </div>
          {isUnknown && onTest ? (
            <Button size="sm" variant="secondary" onClick={() => onTest(axis.axis)} loading={testing}>
              Test this axis
            </Button>
          ) : null}
        </div>
      </CardBody>
    </Card>
  );
}