"use client";

import { useState } from "react";

import { getFilings, getMacroEvents, getMacroSeries, syncFilings, syncMacro } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import type { FilingRecord, MacroEventRecord, MacroSeriesRecord } from "@/lib/types";

interface IntelSyncScreenProps {
  initialFilings: FilingRecord[];
  initialSeries: MacroSeriesRecord[];
  initialEvents: MacroEventRecord[];
}

export function IntelSyncScreen({ initialFilings, initialSeries, initialEvents }: IntelSyncScreenProps) {
  const [filings, setFilings] = useState(initialFilings);
  const [series, setSeries] = useState(initialSeries);
  const [events, setEvents] = useState(initialEvents);
  const [message, setMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function refreshAll() {
    const [nextFilings, nextSeries, nextEvents] = await Promise.all([
      getFilings(),
      getMacroSeries(),
      getMacroEvents(30)
    ]);
    setFilings(nextFilings);
    setSeries(nextSeries);
    setEvents(nextEvents);
  }

  async function onSyncFilings() {
    setIsLoading(true);
    try {
      const summary = await syncFilings();
      await refreshAll();
      setMessage(
        `Filings sync complete: fetched ${summary.fetched_count}, inserted ${summary.inserted_count}, summaries ${summary.updated_summary_count}.`
      );
    } finally {
      setIsLoading(false);
    }
  }

  async function onSyncMacro() {
    setIsLoading(true);
    try {
      const summary = await syncMacro();
      await refreshAll();
      setMessage(
        `Macro sync complete: series ${summary.series_upserted}, events ${summary.events_inserted}.`
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.16em] text-textSecondary">Phase 6</p>
          <h2 className="text-2xl font-semibold text-textPrimary">Filings & Macro Sync</h2>
        </div>
        <div className="ml-auto flex gap-2">
          <button
            type="button"
            className="rounded-md border border-border px-3 py-2 text-xs text-textSecondary hover:text-textPrimary"
            onClick={() => {
              void onSyncFilings();
            }}
            disabled={isLoading}
          >
            Sync Filings
          </button>
          <button
            type="button"
            className="rounded-md border border-border px-3 py-2 text-xs text-textSecondary hover:text-textPrimary"
            onClick={() => {
              void onSyncMacro();
            }}
            disabled={isLoading}
          >
            Sync Macro
          </button>
        </div>
      </div>

      {message ? (
        <div className="rounded-md border border-success/40 bg-success/10 px-3 py-2 text-sm text-success">
          {message}
        </div>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-2">
        <section className="panel">
          <div className="panel-header">
            <h3 className="text-sm font-semibold text-textPrimary">Recent Filings</h3>
          </div>
          <div className="panel-body space-y-2">
            {filings.map((item) => (
              <article key={item.id} className="rounded-md border border-border px-3 py-2">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm text-textPrimary">
                    {item.symbol} · {item.form_type}
                  </p>
                  <p className="text-xs text-textSecondary">{formatDateTime(item.filed_at)}</p>
                </div>
                <p className="mt-1 text-xs text-textSecondary">
                  {item.summary?.summary ?? "No summary available"}
                </p>
              </article>
            ))}
            {filings.length === 0 ? <p className="text-sm text-textSecondary">No filings available.</p> : null}
          </div>
        </section>

        <section className="panel">
          <div className="panel-header">
            <h3 className="text-sm font-semibold text-textPrimary">Macro Series</h3>
          </div>
          <div className="panel-body space-y-2">
            {series.map((item) => (
              <article key={item.id} className="rounded-md border border-border px-3 py-2">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm text-textPrimary">{item.code}</p>
                  <p className="text-xs text-textSecondary">{item.frequency}</p>
                </div>
                <p className="mt-1 text-xs text-textSecondary">{item.name}</p>
                <p className="mt-1 text-xs text-textSecondary">
                  Upcoming events: {item.upcoming_event_count}
                </p>
              </article>
            ))}
            {series.length === 0 ? <p className="text-sm text-textSecondary">No macro series loaded.</p> : null}
          </div>
        </section>
      </div>

      <section className="panel">
        <div className="panel-header">
          <h3 className="text-sm font-semibold text-textPrimary">Upcoming Macro Events</h3>
        </div>
        <div className="panel-body overflow-auto">
          <table className="min-w-full">
            <thead className="text-left text-xs text-textSecondary">
              <tr>
                <th className="table-cell">Time</th>
                <th className="table-cell">Series</th>
                <th className="table-cell">Event</th>
                <th className="table-cell">Impact</th>
                <th className="table-cell">Forecast</th>
              </tr>
            </thead>
            <tbody>
              {events.map((event) => (
                <tr key={event.id} className="border-t border-border">
                  <td className="table-cell text-textSecondary">{formatDateTime(event.scheduled_at)}</td>
                  <td className="table-cell text-textSecondary">{event.series_code ?? "-"}</td>
                  <td className="table-cell text-textPrimary">{event.title}</td>
                  <td className="table-cell text-textSecondary">{event.impact}</td>
                  <td className="table-cell text-textSecondary">{event.forecast ?? "-"}</td>
                </tr>
              ))}
              {events.length === 0 ? (
                <tr>
                  <td className="table-cell text-textSecondary" colSpan={5}>
                    No macro events in selected window.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
