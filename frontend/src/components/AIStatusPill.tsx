"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/Badge";
import type { StatusResponse } from "@/types/api";

export function AIStatusPill() {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const s = await api.status();
        if (!cancelled) {
          setStatus(s);
          setError(null);
        }
      } catch {
        if (!cancelled) setError("offline");
      }
    }
    load();
    const id = setInterval(load, 15_000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  if (error) {
    return (
      <Badge tone="miss" title="Backend unreachable">
        <span className="h-1.5 w-1.5 rounded-full bg-miss" />
        offline
      </Badge>
    );
  }

  if (!status) {
    return (
      <Badge tone="neutral" title="Checking backend…">
        <span className="h-1.5 w-1.5 rounded-full bg-fg-faint" />
        checking
      </Badge>
    );
  }

  const live = status.ai.available;
  return (
    <Badge
      tone={live ? "hit" : "warn"}
      title={
        live
          ? `Provider: ${status.ai.provider}`
          : "AI provider unavailable — running on deterministic fallback"
      }
    >
      <span
        className={`h-1.5 w-1.5 rounded-full ${live ? "bg-hit" : "bg-warn"}`}
      />
      {live ? `live · ${status.ai.provider}` : "fallback mode"}
    </Badge>
  );
}