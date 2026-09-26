import * as React from "react";
import { cn } from "@/lib/cn";

export const Card = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(function Card({ className, ...rest }, ref) {
  return (
    <div
      ref={ref}
      className={cn(
        "rounded-lg border hairline bg-bg-surface/60 backdrop-blur-[1px]",
        className
      )}
      {...rest}
    />
  );
});

export function CardHeader({
  title,
  subtitle,
  action,
  className,
}: {
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex items-start justify-between gap-3 border-b hairline px-4 py-3",
        className
      )}
    >
      <div className="min-w-0">
        <div className="text-sm font-medium tracking-tight">{title}</div>
        {subtitle ? (
          <div className="mt-0.5 text-xs text-fg-muted">{subtitle}</div>
        ) : null}
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </div>
  );
}

export function CardBody({
  className,
  ...rest
}: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("px-4 py-4", className)} {...rest} />;
}