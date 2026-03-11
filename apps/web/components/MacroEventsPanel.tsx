import { formatDateTime } from "@/lib/format";
import type { MacroEvent } from "@/lib/types";

interface MacroEventsPanelProps {
  events: MacroEvent[];
}

const impactClass: Record<MacroEvent["impact"], string> = {
  low: "text-textSecondary",
  medium: "text-warning",
  high: "text-danger"
};

export function MacroEventsPanel({ events }: MacroEventsPanelProps) {
  if (events.length === 0) {
    return <p className="text-sm text-textSecondary">No macro events scheduled.</p>;
  }

  return (
    <ul className="space-y-2">
      {events.map((event) => (
        <li key={event.id} className="rounded-md border border-border px-3 py-2">
          <div className="flex items-center justify-between">
            <p className="text-sm text-textPrimary">{event.title}</p>
            <span className={`text-xs uppercase ${impactClass[event.impact]}`}>{event.impact}</span>
          </div>
          <p className="mt-1 text-xs text-textSecondary">{formatDateTime(event.scheduled_at)}</p>
        </li>
      ))}
    </ul>
  );
}
