"use client";

import { useState } from "react";

import { createJournalEntry, getJournalEntries } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import type { TradeJournalEntry } from "@/lib/types";
import { StateNotice } from "@/components/StateNotice";

interface JournalScreenProps {
  initialEntries: TradeJournalEntry[];
}

interface JournalDraft {
  symbol: string;
  entryType: string;
  title: string;
  body: string;
  tags: string;
}

const defaultDraft: JournalDraft = {
  symbol: "",
  entryType: "observation",
  title: "",
  body: "",
  tags: ""
};

export function JournalScreen({ initialEntries }: JournalScreenProps) {
  const [entries, setEntries] = useState(initialEntries);
  const [draft, setDraft] = useState<JournalDraft>(defaultDraft);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function refresh() {
    const next = await getJournalEntries({ limit: 120 });
    setEntries(next);
  }

  async function onCreateEntry() {
    if (!draft.title.trim() || !draft.body.trim()) {
      setError("Title and body are required.");
      return;
    }

    setIsSaving(true);
    try {
      await createJournalEntry({
        symbol: draft.symbol.trim() ? draft.symbol.trim().toUpperCase() : null,
        entry_type: draft.entryType,
        title: draft.title.trim(),
        body: draft.body.trim(),
        tags: draft.tags
          .split(",")
          .map((token) => token.trim())
          .filter(Boolean)
      });
      setDraft(defaultDraft);
      await refresh();
      setError(null);
      setMessage("Journal entry created.");
    } catch {
      setError("Unable to create journal entry.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <header>
        <p className="text-xs uppercase tracking-[0.16em] text-textSecondary">Phase 9</p>
        <h2 className="text-2xl font-semibold text-textPrimary">Trade Journal</h2>
        <p className="text-xs text-textSecondary">
          Linked observations across transactions, broker order events, and post-mortems.
        </p>
      </header>

      {error ? <StateNotice tone="error" title={error} /> : null}
      {message ? <StateNotice title={message} /> : null}

      <section className="panel">
        <div className="panel-header">
          <h3 className="text-sm font-semibold text-textPrimary">New Entry</h3>
        </div>
        <div className="panel-body grid gap-2 md:grid-cols-2">
          <input
            value={draft.symbol}
            onChange={(event) => setDraft((current) => ({ ...current, symbol: event.target.value }))}
            placeholder="Symbol (optional)"
            className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
          />
          <input
            value={draft.entryType}
            onChange={(event) => setDraft((current) => ({ ...current, entryType: event.target.value }))}
            placeholder="Entry type"
            className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
          />
          <input
            value={draft.title}
            onChange={(event) => setDraft((current) => ({ ...current, title: event.target.value }))}
            placeholder="Title"
            className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary md:col-span-2"
          />
          <textarea
            value={draft.body}
            onChange={(event) => setDraft((current) => ({ ...current, body: event.target.value }))}
            placeholder="Entry body"
            rows={4}
            className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary md:col-span-2"
          />
          <input
            value={draft.tags}
            onChange={(event) => setDraft((current) => ({ ...current, tags: event.target.value }))}
            placeholder="Tags (comma-separated)"
            className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary md:col-span-2"
          />
          <button
            type="button"
            onClick={() => {
              void onCreateEntry();
            }}
            className="rounded-md border border-border px-3 py-2 text-sm text-textSecondary hover:text-textPrimary"
            disabled={isSaving}
          >
            {isSaving ? "Saving..." : "Create Entry"}
          </button>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h3 className="text-sm font-semibold text-textPrimary">Recent Entries</h3>
        </div>
        <div className="panel-body">
          {entries.length === 0 ? (
            <StateNotice title="No journal entries yet." />
          ) : (
            <ul className="space-y-2">
              {entries.map((entry) => (
                <li key={entry.id} className="rounded-md border border-border px-3 py-2">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm text-textPrimary">{entry.title}</p>
                    <p className="text-xs text-textSecondary">{entry.entry_type}</p>
                  </div>
                  <p className="mt-1 text-sm text-textSecondary">{entry.body}</p>
                  <p className="mt-1 text-xs text-textSecondary">
                    {(entry.symbol ?? "GLOBAL").toUpperCase()} · {formatDateTime(entry.created_at)}
                  </p>
                  {entry.tags.length > 0 ? (
                    <p className="mt-1 text-xs text-textSecondary">Tags: {entry.tags.join(", ")}</p>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>
    </div>
  );
}
