"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { MirrorVsYou } from "@/features/comparison/MirrorVsYou";
import type { ResolveResponse } from "@/types/api";

export default function Page() {
  const params = useParams() as { predictionId: string };
  const predictionId = params?.predictionId;
  const [result, setResult] = useState<ResolveResponse | null>(null);
  const [missing, setMissing] = useState(false);

  useEffect(() => {
    if (!predictionId) return;
    const raw = sessionStorage.getItem(`mirror.compare.${predictionId}`);
    if (!raw) {
      setMissing(true);
      return;
    }
    try {
      setResult(JSON.parse(raw) as ResolveResponse);
    } catch {
      setMissing(true);
    }
  }, [predictionId]);

  if (missing) {
    return (
      <Card>
        <CardHeader
          title="Comparison not available"
          subtitle="This comparison was resolved in a different browser session."
        />
        <CardBody className="space-y-3 text-sm">
          <p className="text-fg-muted">
            MIRROR stores the comparison locally in your browser. Refreshing
            this page or opening it in a new tab loses the connection to the
            resolved result.
          </p>
          <div className="flex gap-2">
            <Link href="/dashboard">
              <Button variant="secondary">Back to dashboard</Button>
            </Link>
          </div>
        </CardBody>
      </Card>
    );
  }

  if (!result) {
    return <p className="text-sm text-fg-muted">Loading comparison…</p>;
  }

  return (
    <div className="flex flex-col gap-6">
      <MirrorVsYou result={result} />
      <div className="flex flex-wrap justify-end gap-2">
        <Link href="/blindspots">
          <Button variant="secondary">Find my blind spots</Button>
        </Link>
        <Link href="/dashboard">
          <Button>Back to dashboard</Button>
        </Link>
      </div>
    </div>
  );
}