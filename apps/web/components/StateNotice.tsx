interface StateNoticeProps {
  tone?: "info" | "warning" | "error";
  title: string;
  detail?: string;
}

export function StateNotice({ tone = "info", title, detail }: StateNoticeProps) {
  const toneClasses: Record<NonNullable<StateNoticeProps["tone"]>, string> = {
    info: "border-border bg-panelMuted/40 text-textSecondary",
    warning: "border-warning/40 bg-warning/10 text-warning",
    error: "border-danger/40 bg-danger/10 text-danger"
  };

  return (
    <div className={`rounded-md border px-3 py-2 text-sm ${toneClasses[tone]}`}>
      <p className="font-medium">{title}</p>
      {detail ? <p className="mt-1 text-xs opacity-90">{detail}</p> : null}
    </div>
  );
}
