"use client";
import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";

export default function Page() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-serif text-3xl tracking-tight">Before you start</h1>
      </div>
      <Card>
        <CardHeader title="What MIRROR does" />
        <CardBody className="text-sm text-fg-muted">
          MIRROR observes how you make decisions inside short scenarios, builds
          a computational model of your observable behavior, and lets you test
          its predictions against reality.
        </CardBody>
      </Card>
      <Card>
        <CardHeader title="What MIRROR does not do" />
        <CardBody className="text-sm text-fg-muted">
          It does not read your mind, diagnose your personality, assess your
          mental health, or score your intelligence. Every output is a
          probabilistic estimate based on observed behavior.
        </CardBody>
      </Card>
      <div className="flex gap-2">
        <Link href="/calibrate">
          <Button>Continue to calibration</Button>
        </Link>
        <Link href="/dashboard">
          <Button variant="secondary">Skip to dashboard</Button>
        </Link>
      </div>
    </div>
  );
}