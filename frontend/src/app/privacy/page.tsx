"use client";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";

export default function Page() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-serif text-3xl tracking-tight">Privacy</h1>
        <p className="mt-1 text-sm text-fg-muted">
          What MIRROR collects, and what it never touches.
        </p>
      </div>

      <Card>
        <CardHeader title="What we collect" />
        <CardBody className="text-sm text-fg-muted">
          Only interactions inside this application: which options you view,
          when you view them, how long you take to decide, whether you open
          additional information, and your final choice. All of this is
          stored in your local database under a random user id.
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="What we never collect" />
        <CardBody className="text-sm text-fg-muted">
          No camera. No microphone. No face or biometrics. No browser history.
          No external contacts. No private files. No IP-derived location.
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Delete my data" />
        <CardBody className="text-sm text-fg-muted">
          Use <span className="font-mono">DELETE /api/profile/&#123;user_id&#125;</span> to
          permanently erase every trace of your MIRROR, including all events
          and decisions.
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="What MIRROR is not" />
        <CardBody className="text-sm text-fg-muted">
          MIRROR models observable interaction behavior inside the application.
          It does not read thoughts or infer private mental states. It does not
          diagnose personality, mental health, or intelligence.
        </CardBody>
      </Card>
    </div>
  );
}