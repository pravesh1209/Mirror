"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";

export function DemoBanner() {
  const router = useRouter();
  const [isDemo, setIsDemo] = useState(false);

  useEffect(() => {
    const check = () => {
      setIsDemo(localStorage.getItem("mirror.demo") === "1");
    };
    check();
    // recheck on navigation (soft route changes don't remount this on their own)
    const id = setInterval(check, 1000);
    return () => clearInterval(id);
  }, []);

  if (!isDemo) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      className="border-b border-accent/30 bg-accent/5"
    >
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-2 text-xs">
        <div className="flex items-center gap-2">
          <span
            aria-hidden
            className="inline-block h-1.5 w-1.5 rounded-full bg-accent"
          />
          <span className="text-fg">
            You are viewing{" "}
            <span className="font-mono uppercase tracking-wider">
              DEMO DATA
            </span>
            . Nothing on these screens reflects a real user.
          </span>
        </div>
        <Button
          size="sm"
          variant="ghost"
          onClick={async () => {
            try {
              const { api } = await import("@/lib/api");
              await api.resetDemo();
            } catch {
              // best-effort
            }
            localStorage.removeItem("mirror.demo");
            localStorage.removeItem("mirror.user");
            localStorage.removeItem("mirror.session");
            router.push("/");
          }}
        >
          Exit demo
        </Button>
      </div>
    </div>
  );
}