"use client";

import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/cn";

interface Props {
  limitSec: number;
  /** Called once when the timer reaches 0. */
  onExpire: () => void;
  /** Reset the timer when this changes (e.g. a new scenario id). */
  resetKey: string;
}

export function DecisionTimer({ limitSec, onExpire, resetKey }: Props) {
  const [remaining, setRemaining] = useState(limitSec);
  const firedRef = useRef(false);

  useEffect(() => {
    firedRef.current = false;
    setRemaining(limitSec);
  }, [limitSec, resetKey]);

  useEffect(() => {
    const id = setInterval(() => {
      setRemaining((r) => {
        if (r <= 1) {
          clearInterval(id);
          if (!firedRef.current) {
            firedRef.current = true;
            onExpire();
          }
          return 0;
        }
        return r - 1;
      });
    }, 1000);
    return () => clearInterval(id);
  }, [onExpire, resetKey]);

  const danger = remaining <= Math.max(5, Math.floor(limitSec * 0.25));
  const ratio = limitSec > 0 ? remaining / limitSec : 0;

  return (
    <div className="flex items-center gap-3 text-xs text-fg-muted">
      <span
        className={cn(
          "font-mono tabular-nums",
          danger ? "text-miss" : "text-fg"
        )}
        aria-live="polite"
      >
        {String(Math.floor(remaining / 60)).padStart(2, "0")}:
        {String(remaining % 60).padStart(2, "0")}
      </span>
      <div className="h-0.5 w-24 overflow-hidden rounded bg-line/15">
        <div
          className={cn(
            "h-full transition-[width] duration-1000 ease-linear",
            danger ? "bg-miss" : "bg-accent"
          )}
          style={{ width: `${ratio * 100}%` }}
        />
      </div>
    </div>
  );
}