import { formatDateTime } from "@/lib/format";
import type { MorningBrief } from "@/lib/types";

interface MorningBriefCardProps {
  brief: MorningBrief;
}

export function MorningBriefCard({ brief }: MorningBriefCardProps) {
  return (
    <div className="rounded-lg border border-accent/30 bg-accent/5 p-4">
      <p className="text-xs uppercase tracking-wider text-accent">Morning Brief</p>
      <h3 className="mt-2 text-base font-semibold text-textPrimary">{brief.headline}</h3>
      <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-textSecondary">
        {brief.bullets.map((bullet, index) => (
          <li key={`${brief.id}-${index}`}>{bullet}</li>
        ))}
      </ul>
      <p className="mt-3 text-xs text-textSecondary">Generated {formatDateTime(brief.generated_at)}</p>
    </div>
  );
}
