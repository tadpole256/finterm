export default function Loading() {
  return (
    <div className="space-y-4" role="status" aria-live="polite">
      <div className="h-6 w-56 animate-pulse rounded bg-panelMuted" />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <div className="h-40 animate-pulse rounded-xl border border-border bg-panel" />
        <div className="h-40 animate-pulse rounded-xl border border-border bg-panel" />
        <div className="h-40 animate-pulse rounded-xl border border-border bg-panel" />
      </div>
      <p className="text-sm text-textSecondary">Loading workspace data...</p>
    </div>
  );
}
