"use client";

import { useEffect, useRef } from "react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { DecisionTimer } from "./DecisionTimer";
import { InfoDrawer } from "./InfoDrawer";
import { OptionCard } from "./OptionCard";
import { ConfidenceSlider } from "./ConfidenceSlider";
import { useScenarioSession } from "@/hooks/useScenarioSession";
import type { DecisionResponse, ScenarioOut } from "@/types/api";

interface Props {
  sessionId: string;
  scenario: ScenarioOut;
  onComplete?: (decision: DecisionResponse) => void;
  submitLabel?: string;
}

export function ScenarioPlayer({
  sessionId,
  scenario,
  onComplete,
  submitLabel = "Submit decision",
}: Props) {
  const session = useScenarioSession({ sessionId, scenario, onComplete });
  const autoSubmitted = useRef(false);

  // Auto-submit if timer expires and a choice exists
  useEffect(() => {
    if (
      scenario.time_limit_sec &&
      session.phase === "playing" &&
      !autoSubmitted.current
    ) {
      // timer component handles the actual trigger via onExpire
    }
  }, [scenario.time_limit_sec, session.phase]);

  const onTimerExpire = () => {
    if (autoSubmitted.current) return;
    autoSubmitted.current = true;
    if (session.chosenId) {
      void session.submit();
    } else if (scenario.options[0]) {
      session.select(scenario.options[0].id);
      // give React a beat, then submit
      setTimeout(() => void session.submit(), 50);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      {/* HEADER */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-3">
            <Badge tone="accent">{scenario.domain}</Badge>
            {scenario.has_reveal ? (
              <Badge tone="warn">info updates mid-scenario</Badge>
            ) : null}
            {scenario.source === "llm" ? (
              <Badge tone="neutral">ai-generated</Badge>
            ) : null}
          </div>
          <h1 className="mt-3 font-serif text-2xl tracking-tight">
            {scenario.title}
          </h1>
        </div>
        <div className="flex items-center gap-3">
          {scenario.time_limit_sec ? (
            <DecisionTimer
              limitSec={scenario.time_limit_sec}
              resetKey={scenario.id}
              onExpire={onTimerExpire}
            />
          ) : null}
          <Button
            size="sm"
            variant="ghost"
            onClick={session.openInfo}
            aria-label="Open additional information"
          >
            More info
          </Button>
        </div>
      </div>

      {/* BODY */}
      <p className="max-w-3xl text-sm leading-relaxed text-fg-muted">
        {scenario.body}
      </p>

      {/* OPTIONS */}
      <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
        {scenario.options.map((opt) => (
          <OptionCard
            key={opt.id}
            option={opt}
            selected={session.chosenId === opt.id}
            onSelect={() => session.select(opt.id)}
            onView={() => session.viewOption(opt.id)}
          />
        ))}
      </div>

      {/* FOOTER */}
      <div className="sticky bottom-0 -mx-4 mt-2 border-t hairline bg-bg/90 px-4 py-4 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <ConfidenceSlider
            value={session.confidence}
            onChange={session.setConfidence}
          />
          <div className="flex items-center gap-3">
            <span className="text-[11px] text-fg-faint">
              {session.viewedCount} option
              {session.viewedCount === 1 ? "" : "s"} inspected
              {session.pending > 0 ? ` · ${session.pending} events queued` : ""}
            </span>
            <Button
              onClick={() => void session.submit()}
              disabled={!session.chosenId || session.phase === "submitting"}
              loading={session.phase === "submitting"}
            >
              {submitLabel}
            </Button>
          </div>
        </div>
        {session.errorMessage ? (
          <p className="mt-2 text-xs text-miss" role="alert">
            {session.errorMessage}
          </p>
        ) : null}
      </div>

      <InfoDrawer
        open={session.infoOpen}
        scenario={scenario}
        revealShown={session.revealShown}
        onClose={session.closeInfo}
      />
    </div>
  );
}