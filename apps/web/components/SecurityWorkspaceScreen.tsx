"use client";

import { useState } from "react";

import { FreshnessPill } from "@/components/FreshnessPill";
import { Panel } from "@/components/Panel";
import { SecurityChart } from "@/components/SecurityChart";
import { getSecurityWorkspace } from "@/lib/api";
import { formatCompact, formatCurrency, formatDate, formatPercent } from "@/lib/format";
import type { SecurityWorkspacePayload } from "@/lib/types";

interface SecurityWorkspaceScreenProps {
  data: SecurityWorkspacePayload;
}

const timeframes = [
  { label: "1M", value: "1M" },
  { label: "3M", value: "3M" },
  { label: "6M", value: "6M" },
  { label: "1Y", value: "1Y" }
] as const;

export function SecurityWorkspaceScreen({ data }: SecurityWorkspaceScreenProps) {
  const [timeframe, setTimeframe] = useState<(typeof timeframes)[number]["value"]>("6M");
  const [workspaceData, setWorkspaceData] = useState(data);
  const [isLoadingTimeframe, setIsLoadingTimeframe] = useState(false);
  const [showSma20, setShowSma20] = useState(true);
  const [showSma50, setShowSma50] = useState(true);
  const [showEma20, setShowEma20] = useState(false);
  const [showRsi, setShowRsi] = useState(true);
  const [showMacd, setShowMacd] = useState(true);

  async function onSelectTimeframe(next: (typeof timeframes)[number]["value"]) {
    setTimeframe(next);
    setIsLoadingTimeframe(true);
    const payload = await getSecurityWorkspace(workspaceData.instrument.symbol, next);
    setWorkspaceData(payload);
    setIsLoadingTimeframe(false);
  }

  return (
    <div className="space-y-6">
      <header className="panel p-5">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-textSecondary">Security Workspace</p>
            <h2 className="mt-1 text-2xl font-semibold text-textPrimary">
              {workspaceData.instrument.symbol} · {workspaceData.instrument.name}
            </h2>
            <p className="mt-1 text-sm text-textSecondary">
              {workspaceData.instrument.exchange} · {workspaceData.instrument.sector ?? "Sector N/A"} · {workspaceData.instrument.industry ?? "Industry N/A"}
            </p>
          </div>
          <FreshnessPill
            status={workspaceData.freshness_status}
            asOf={workspaceData.as_of}
            delaySeconds={workspaceData.delay_seconds}
          />
        </div>

        <div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <div>
            <p className="kpi-label">Last Price</p>
            <p className="kpi-value">{formatCurrency(workspaceData.quote.price)}</p>
          </div>
          <div>
            <p className="kpi-label">Session Change</p>
            <p className={`kpi-value ${workspaceData.quote.change_percent >= 0 ? "text-success" : "text-danger"}`}>
              {formatPercent(workspaceData.quote.change_percent)}
            </p>
          </div>
          <div>
            <p className="kpi-label">Market Cap</p>
            <p className="kpi-value">{formatCompact(workspaceData.instrument.market_cap)}</p>
          </div>
          <div>
            <p className="kpi-label">Watchlists</p>
            <p className="kpi-value">{workspaceData.watchlists.filter((item) => item.is_member).length}</p>
          </div>
        </div>
      </header>

      <Panel title="Price + Technicals" subtitle="Candles, volume, and overlays">
        <div className="mb-3 flex flex-wrap items-center gap-2">
          {timeframes.map((item) => (
            <button
              key={item.value}
              type="button"
              className={`rounded-md px-3 py-1 text-xs ${
                timeframe === item.value
                  ? "bg-accent text-[#06121e]"
                  : "border border-border text-textSecondary"
              }`}
              onClick={() => {
                void onSelectTimeframe(item.value);
              }}
            >
              {item.label}
            </button>
          ))}
          <span className="mx-2 h-5 w-px bg-border" />
          <Toggle checked={showSma20} onChange={setShowSma20} label="SMA 20" />
          <Toggle checked={showSma50} onChange={setShowSma50} label="SMA 50" />
          <Toggle checked={showEma20} onChange={setShowEma20} label="EMA 20" />
          <Toggle checked={showRsi} onChange={setShowRsi} label="RSI 14" />
          <Toggle checked={showMacd} onChange={setShowMacd} label="MACD" />
        </div>

        <SecurityChart
          data={workspaceData}
          showSma20={showSma20}
          showSma50={showSma50}
          showEma20={showEma20}
          showRsi={showRsi}
          showMacd={showMacd}
        />

        <p className="mt-2 text-xs text-textSecondary">
          Selected timeframe: {timeframe}
          {isLoadingTimeframe ? " · updating bars..." : ""}
        </p>
      </Panel>

      <div className="grid gap-6 lg:grid-cols-3">
        <Panel title="Recent Filings" subtitle="Most recent document updates">
          <ul className="space-y-2">
            {workspaceData.filings.map((filing) => (
              <li key={filing.id} className="rounded-md border border-border px-3 py-2">
                <p className="text-sm font-medium text-textPrimary">{filing.form_type}</p>
                <p className="mt-1 text-xs text-textSecondary">{formatDate(filing.filed_at)}</p>
                <p className="mt-1 text-xs text-textSecondary">{filing.summary ?? "No summary yet"}</p>
              </li>
            ))}
          </ul>
        </Panel>

        <Panel title="Recent Notes" subtitle="Linked research context">
          <ul className="space-y-2">
            {workspaceData.notes.map((note) => (
              <li key={note.id} className="rounded-md border border-border px-3 py-2">
                <p className="text-sm text-textPrimary">{note.title}</p>
                <p className="mt-1 text-xs text-textSecondary">{note.note_type}</p>
                <p className="mt-1 text-xs text-textSecondary">Updated {formatDate(note.updated_at)}</p>
              </li>
            ))}
          </ul>
        </Panel>

        <Panel title="Catalysts + What Changed" subtitle="Event timeline and AI delta placeholder">
          <ul className="space-y-2">
            {workspaceData.catalysts.map((event) => (
              <li key={event.id} className="rounded-md border border-border px-3 py-2">
                <p className="text-sm text-textPrimary">{event.title}</p>
                <p className="mt-1 text-xs text-textSecondary">{formatDate(event.event_date)} · {event.status}</p>
              </li>
            ))}
          </ul>
          <div className="mt-4 rounded-md border border-accent/30 bg-accent/5 p-3 text-sm text-textSecondary">
            {workspaceData.what_changed}
          </div>
        </Panel>
      </div>
    </div>
  );
}

interface ToggleProps {
  checked: boolean;
  onChange: (value: boolean) => void;
  label: string;
}

function Toggle({ checked, onChange, label }: ToggleProps) {
  return (
    <button
      type="button"
      className={`rounded-md border px-2 py-1 text-xs ${
        checked ? "border-accent text-accent" : "border-border text-textSecondary"
      }`}
      onClick={() => onChange(!checked)}
    >
      {label}
    </button>
  );
}
