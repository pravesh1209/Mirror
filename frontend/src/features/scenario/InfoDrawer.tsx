"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/Button";
import type { ScenarioOut } from "@/types/api";

interface Props {
  open: boolean;
  scenario: ScenarioOut;
  revealShown: boolean;
  onClose: () => void;
}

export function InfoDrawer({ open, scenario, revealShown, onClose }: Props) {
  // ESC to close
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  const revealInfo = scenario.reveal_payload?.info;

  return (
    <div
      className="fixed inset-0 z-40 flex items-end justify-center bg-bg/60 backdrop-blur-sm sm:items-center"
      role="dialog"
      aria-modal="true"
      aria-label="Additional information"
      onClick={onClose}
    >
      <div
        className="w-full max-w-lg rounded-t-lg border hairline bg-bg-surface p-5 sm:rounded-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="text-sm font-medium tracking-tight">
              Additional information
            </h3>
            <p className="mt-0.5 text-xs text-fg-muted">
              {revealShown && revealInfo
                ? "New information arrived mid-scenario."
                : "General context for this scenario."}
            </p>
          </div>
          <Button size="sm" variant="ghost" onClick={onClose}>
            Close
          </Button>
        </div>

        <div className="mt-4 space-y-4 text-sm text-fg-muted">
          {revealShown && revealInfo ? (
            <div className="rounded-md border border-accent/30 bg-accent/5 p-3 text-fg">
              <div className="text-[10px] uppercase tracking-widest text-accent">
                Update
              </div>
              <p className="mt-1">{revealInfo}</p>
            </div>
          ) : null}

          <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
            <Row label="Domain" value={scenario.domain} />
            <Row
              label="Difficulty"
              value={scenario.attributes.difficulty.toFixed(2)}
            />
            <Row
              label="Time pressure"
              value={scenario.attributes.time_pressure.toFixed(2)}
            />
            <Row
              label="Uncertainty"
              value={scenario.attributes.uncertainty.toFixed(2)}
            />
            <Row
              label="Information availability"
              value={scenario.attributes.information_availability.toFixed(2)}
            />
          </dl>

          <p className="text-xs">
            Values are structural attributes of the scenario, not judgments
            about you. MIRROR uses them to place this scenario in context.
          </p>
        </div>
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <dt className="text-[10px] uppercase tracking-widest text-fg-faint">
        {label}
      </dt>
      <dd className="font-mono text-fg">{value}</dd>
    </div>
  );
}