import Link from "next/link";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

export function Placeholder({
  title,
  subtitle,
  body,
}: {
  title: string;
  subtitle: string;
  body: string;
}) {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-serif text-3xl tracking-tight">{title}</h1>
        <p className="mt-1 text-sm text-fg-muted">{subtitle}</p>
      </div>
      <Card>
        <CardHeader title="Coming online in the next build step" />
        <CardBody className="space-y-4 text-sm text-fg-muted">
          <p>{body}</p>
          <div className="flex flex-wrap gap-2">
            <Link href="/dashboard">
              <Button variant="secondary">Back to dashboard</Button>
            </Link>
            <Link href="/calibrate">
              <Button>Start calibration</Button>
            </Link>
          </div>
        </CardBody>
      </Card>
    </div>
  );
}