const STEPS = ["observe", "learn", "predict", "test", "adapt"] as const;

export function LoopAnimation() {
  return (
    <div className="flex items-center justify-between gap-1 text-[11px] font-mono uppercase tracking-widest text-fg-muted">
      {STEPS.map((step, i) => (
        <div key={step} className="flex items-center gap-1">
          <span
            className="animate-flow-x"
            style={{ animationDelay: `${i * 0.4}s` }}
          >
            {step}
          </span>
          {i < STEPS.length - 1 ? (
            <span aria-hidden className="text-fg-faint">
              →
            </span>
          ) : null}
        </div>
      ))}
      <span aria-hidden className="hidden text-fg-faint sm:inline">
        ↺
      </span>
    </div>
  );
}