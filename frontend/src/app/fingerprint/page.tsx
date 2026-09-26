"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { FingerprintView } from "@/features/fingerprint/FingerprintView";
import { api, MirrorApiError } from "@/lib/api";
import type { FingerprintResponse } from "@/types/api";

export default function Page() {
  const [fp, setFp] = useState<FingerprintResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const uid = localStorage.getItem("mirror.user");
    if (!uid) {
      setLoading(false);
      return;
    }
    (async () => {
      try {
        const data = await api.getFingerprint(uid);
        setFp(data);
      } catch (e) {
        setError(
          e instanceof MirrorApiError
            ? `${e.status}: ${e.message}`
            : "Backend unreachable."
        );
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <p className="text-sm text-fg-muted">Loading…</p>;

  if (!fp) {
    return (
      <Card>
        <CardHeader
          title="No MIRROR yet"
          subtitle={
            error ??
            "Complete at least one calibration scenario to see your fingerprint."
          }
        />
        <CardBody className="flex gap-2">
          <Link href="/">
            <Button variant="secondary">Back to landing</Button>
          </Link>
          <Link href="/calibrate">
            <Button>Start calibration</Button>
          </Link>
        </CardBody>
      </Card>
    );
  }

  return <FingerprintView fp={fp} />;
}