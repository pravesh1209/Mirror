"use client";

interface Props {
  value: number;
  onChange: (value: number) => void;
}

const ANCHORS: { at: number; label: string }[] = [
  { at: 0.1, label: "guessing" },
  { at: 0.5, label: "fairly sure" },
  { at: 0.9, label: "very sure" },
];

export function ConfidenceSlider({ value, onChange }: Props) {
  const pct = Math.round(value * 100);
  const anchor = [...ANCHORS].reverse().find((a) => value >= a.at)?.label ?? "unsure";

  return (
    <div className="flex flex-col gap-1">
      <label
        htmlFor="decision-confidence"
        className="text-[11px] uppercase tracking-widest text-fg-faint"
      >
        How confident are you in this choice?
      </label>
      <div className="flex items-center gap-3">
        <input
          id="decision-confidence"
          type="range"
          min={0}
          max={1}
          step={0.05}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          aria-label="Your confidence in this specific decision"
          aria-valuetext={`${pct} percent — ${anchor}`}
          className="h-1 w-48 accent-accent"
        />
        <span className="w-20 shrink-0 font-mono text-xs text-fg">
          {pct}% · {anchor}
        </span>
      </div>
    </div>
  );
}