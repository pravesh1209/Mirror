import * as React from "react";
import { cn } from "@/lib/cn";

type Tone = "neutral" | "accent" | "hit" | "warn" | "miss";

const toneClasses: Record<Tone, string> = {
  neutral: "text-fg-muted border hairline",
  accent: "text-accent border-accent/30 bg-accent/5",
  hit: "text-hit border-hit/30 bg-hit/5",
  warn: "text-warn border-warn/30 bg-warn/5",
  miss: "text-miss border-miss/30 bg-miss/5",
};

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  tone?: Tone;
}

export function Badge({ tone = "neutral", className, children, ...rest }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider",
        toneClasses[tone],
        className
      )}
      {...rest}
    >
      {children}
    </span>
  );
}