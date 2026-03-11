import { formatDateTime } from "@/lib/format";
import { StateNotice } from "@/components/StateNotice";
import type { AlertDigestItem } from "@/lib/types";

interface AlertsPanelProps {
  alerts: AlertDigestItem[];
}

export function AlertsPanel({ alerts }: AlertsPanelProps) {
  if (alerts.length === 0) {
    return <StateNotice title="No active alerts." detail="Create rules in Alerts to populate this panel." />;
  }

  return (
    <ul className="space-y-2">
      {alerts.map((alert) => (
        <li key={alert.id} className="rounded-md border border-border px-3 py-2">
          <div className="flex items-center justify-between gap-2">
            <p className="text-sm font-medium text-textPrimary">{alert.symbol}</p>
            <span className="rounded-full border border-border px-2 py-1 text-xs text-textSecondary">
              {alert.status}
            </span>
          </div>
          <p className="mt-1 text-xs text-textSecondary">{alert.rule_summary}</p>
          {alert.triggered_at ? (
            <p className="mt-1 text-xs text-textSecondary">Last trigger: {formatDateTime(alert.triggered_at)}</p>
          ) : null}
        </li>
      ))}
    </ul>
  );
}
