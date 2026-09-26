"use client";
import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { api, MirrorApiError } from "@/lib/api";

export default function Page() {
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function deleteMe() {
    const uid = localStorage.getItem("mirror.user");
    if (!uid) {
      setMsg("No active MIRROR to delete.");
      return;
    }
    setBusy(true);
    try {
      await api.deleteProfile(uid);
      localStorage.removeItem("mirror.user");
      localStorage.removeItem("mirror.session");
      setMsg("Your MIRROR has been deleted.");
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
        <h1 className="font-serif text-3xl tracking-tight">Settings</h1>
      </div>
      <Card>
        <CardHeader title="Delete my data" subtitle="Hard delete, cascades everything" />
        <CardBody className="space-y-3 text-sm text-fg-muted">
          <p>
            This permanently removes your user, sessions, decisions, events,
            feature rows, profiles, predictions, blind spots, and model
            updates. There is no undo.
          </p>
          <Button variant="danger" onClick={deleteMe} loading={busy}>
            Delete my MIRROR
          </Button>
          {msg ? <p className="text-xs text-fg">{msg}</p> : null}
        </CardBody>
      </Card>
    </div>
  );
}