"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { DemoRunner } from "@/features/demo/DemoRunner";
import { api, MirrorApiError } from "@/lib/api";

export default function Page() {
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function reset() {
    setBusy(true);
    setMsg(null);
    try {
      const res = await api.resetDemo();
      localStorage.removeItem("mirror.user");
      localStorage.removeItem("mirror.session");
      setMsg(`Removed ${res.users_deleted} demo user(s). Local state cleared.`);
    } catch (e) {
      setMsg(
        e instanceof MirrorApiError
          ? `${e.status}: ${e.message}`
          : "Backend unreachable."
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-serif text-3xl tracking-tight">Demo Mode</h1>
        <p className="mt-1 text-sm text-fg-muted">
          Everything here is deterministic. The demo makes zero AI API calls.
        </p>
      </div>

      <DemoRunner />

      <Card>
        <CardHeader
          title="Reset demo data"
          subtitle="Deletes only users flagged is_demo=true."
        />
        <CardBody className="space-y-3 text-sm text-fg-muted">
          <p>
            Your real (non-demo) profiles are not touched. Use this before a
            fresh run.
          </p>
          <Button variant="danger" onClick={reset} loading={busy}>
            Reset demo data
          </Button>
          {msg ? <p className="text-xs text-fg">{msg}</p> : null}
        </CardBody>
      </Card>
    </div>
  );
}