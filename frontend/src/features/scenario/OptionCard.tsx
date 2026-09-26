"use client";

import { cn } from "@/lib/cn";
import type { OptionOut } from "@/types/api";

interface Props {
  option: OptionOut;
  selected: boolean;
  onSelect: () => void;
  onView: () => void;
}

export function OptionCard({ option, selected, onSelect, onView }: Props) {
  return (
    <button
      type="button"
      onMouseEnter={onView}
      onFocus={onView}
      onClick={() => {
        onView();
        onSelect();
      }}
      aria-pressed={selected}
      className={cn(
        "group flex h-full w-full flex-col gap-3 rounded-lg border p-4 text-left transition-all",
        "focus-visible:outline-none",
        selected
          ? "border-accent/60 bg-accent/5 ring-1 ring-accent/30"
          : "hairline bg-bg-surface/60 hover:border-accent/30"
      )}
    >
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span
            className={cn(
              "grid h-7 w-7 place-items-center rounded-full border text-xs font-medium",
              selected
                ? "border-accent bg-accent text-bg"
                : "hairline text-fg-muted"
            )}
          >
            {option.label}
          </span>
          <span className="text-sm font-medium tracking-tight">
            {option.title}
          </span>
        </div>
        {option.is_novel ? (
          <span className="text-[10px] uppercase tracking-widest text-fg-faint">
            novel
          </span>
        ) : null}
      </div>

      <p className="text-sm text-fg-muted">{option.description}</p>

      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-[10px] uppercase tracking-widest text-fg-faint">
        <Attr label="risk" value={option.attributes.risk} />
        <Attr label="reward" value={option.attributes.reward} />
        <Attr label="time" value={option.attributes.time_cost} />
        <Attr label="info" value={option.attributes.info_availability} />
      </div>
    </button>
  );
}

function Attr({ label, value }: { label: string; value: number }) {
  const pct = Math.round(Math.max(0, Math.min(1, value)) * 100);
  return (
    <div className="flex items-center gap-2">
      <span className="w-10 shrink-0">{label}</span>
      <span className="h-0.5 flex-1 overflow-hidden rounded bg-line/15">
        <span
          className="block h-full bg-fg-muted/70"
          style={{ width: `${pct}%` }}
        />
      </span>
      <span className="font-mono text-[10px] text-fg-muted">{pct}</span>
    </div>
  );
}