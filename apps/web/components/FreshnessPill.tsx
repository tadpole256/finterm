import type { FreshnessStatus } from "@/lib/types";

const STATUS_CLASSES: Record<FreshnessStatus, string> = {
  fresh: "border-success/40 bg-success/10 text-success",
  stale: "border-warning/40 bg-warning/10 text-warning",
  degraded: "border-danger/40 bg-danger/10 text-danger"
};

interface FreshnessPillProps {
  status: FreshnessStatus;
  asOf: string;
  delaySeconds: number;
}

export function FreshnessPill({ status, asOf, delaySeconds }: FreshnessPillProps) {
  return (
    <span className={`rounded-full border px-2 py-1 text-xs font-medium ${STATUS_CLASSES[status]}`}>
      {status.toUpperCase()} · {Math.round(delaySeconds / 60)}m delay · {new Date(asOf).toLocaleTimeString()}
    </span>
  );
}
