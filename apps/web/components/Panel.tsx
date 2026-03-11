import type { ReactNode } from "react";

interface PanelProps {
  title: string;
  subtitle?: string;
  rightSlot?: ReactNode;
  children: ReactNode;
  className?: string;
}

export function Panel({ title, subtitle, rightSlot, children, className }: PanelProps) {
  return (
    <section className={`panel ${className ?? ""}`}>
      <div className="panel-header flex items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-textPrimary">{title}</h2>
          {subtitle ? <p className="text-xs text-textSecondary">{subtitle}</p> : null}
        </div>
        {rightSlot}
      </div>
      <div className="panel-body">{children}</div>
    </section>
  );
}
