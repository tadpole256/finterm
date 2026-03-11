import { AlertsPanel } from "@/components/AlertsPanel";
import { FreshnessPill } from "@/components/FreshnessPill";
import { MacroEventsPanel } from "@/components/MacroEventsPanel";
import { MarketSnapshotStrip } from "@/components/MarketSnapshotStrip";
import { MorningBriefCard } from "@/components/MorningBriefCard";
import { MoversPanel } from "@/components/MoversPanel";
import { Panel } from "@/components/Panel";
import { WatchlistTable } from "@/components/WatchlistTable";
import type { DashboardPayload } from "@/lib/types";

interface DashboardScreenProps {
  data: DashboardPayload;
}

export function DashboardScreen({ data }: DashboardScreenProps) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.16em] text-textSecondary">Home</p>
          <h2 className="text-2xl font-semibold">Market Dashboard</h2>
        </div>
        <FreshnessPill
          status={data.freshness_status}
          asOf={data.as_of}
          delaySeconds={data.delay_seconds}
        />
      </div>

      <MarketSnapshotStrip quotes={data.market_snapshot} />

      <div className="grid gap-6 xl:grid-cols-[2fr,1fr]">
        <Panel title="Watchlists" subtitle="Linked to latest quote snapshots">
          <WatchlistTable watchlists={data.watchlists} />
        </Panel>

        <Panel title="Morning Brief" subtitle="AI-assisted summary">
          <MorningBriefCard brief={data.morning_brief} />
        </Panel>
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <Panel title="Market Movers" subtitle="Session leaders and laggards" className="xl:col-span-1">
          <MoversPanel gainers={data.movers.gainers} losers={data.movers.losers} />
        </Panel>
        <Panel title="Macro Calendar" subtitle="Today and near-term releases" className="xl:col-span-1">
          <MacroEventsPanel events={data.macro_events} />
        </Panel>
        <Panel title="Active Alerts" subtitle="Open rules and recent triggers" className="xl:col-span-1">
          <AlertsPanel alerts={data.active_alerts} />
        </Panel>
      </div>
    </div>
  );
}
