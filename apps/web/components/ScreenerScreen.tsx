"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";

import {
  createSavedScreen,
  deleteSavedScreen,
  runSavedScreen,
  runScreener
} from "@/lib/api";
import { formatCompact, formatCurrency, formatPercent } from "@/lib/format";
import type { SavedScreen, ScreenerFilters, ScreenerResult, Watchlist } from "@/lib/types";
import { StateNotice } from "@/components/StateNotice";

interface ScreenerScreenProps {
  initialResults: ScreenerResult[];
  initialSavedScreens: SavedScreen[];
  watchlists: Watchlist[];
}

interface FilterDraft {
  symbol_query: string;
  sector: string;
  asset_type: string;
  watchlist_id: string;
  tag: string;
  price_min: string;
  price_max: string;
  market_cap_min: string;
  market_cap_max: string;
  change_percent_min: string;
  change_percent_max: string;
  volume_min: string;
  volume_max: string;
  sort_by: "symbol" | "name" | "price" | "change_percent" | "market_cap" | "volume";
  sort_direction: "asc" | "desc";
  limit: string;
}

const defaultDraft: FilterDraft = {
  symbol_query: "",
  sector: "",
  asset_type: "",
  watchlist_id: "",
  tag: "",
  price_min: "",
  price_max: "",
  market_cap_min: "",
  market_cap_max: "",
  change_percent_min: "",
  change_percent_max: "",
  volume_min: "",
  volume_max: "",
  sort_by: "symbol",
  sort_direction: "asc",
  limit: "150"
};

export function ScreenerScreen({ initialResults, initialSavedScreens, watchlists }: ScreenerScreenProps) {
  const [results, setResults] = useState(initialResults);
  const [savedScreens, setSavedScreens] = useState(initialSavedScreens);
  const [draft, setDraft] = useState<FilterDraft>(defaultDraft);
  const [saveName, setSaveName] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const symbolInputRef = useRef<HTMLInputElement | null>(null);

  const sectors = useMemo(
    () =>
      Array.from(
        new Set(
          initialResults
            .map((item) => item.sector)
            .filter((value): value is string => Boolean(value))
        )
      ),
    [initialResults]
  );

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      const target = event.target as HTMLElement | null;
      const isTypingTarget =
        target instanceof HTMLInputElement ||
        target instanceof HTMLTextAreaElement ||
        (target?.isContentEditable ?? false);

      if (event.key === "/" && !isTypingTarget) {
        event.preventDefault();
        symbolInputRef.current?.focus();
        return;
      }

      if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
        event.preventDefault();
        void onRunScreener();
        return;
      }

      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "s") {
        event.preventDefault();
        void onSaveScreen();
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  });

  function parseNumber(value: string): number | undefined {
    if (!value.trim()) {
      return undefined;
    }
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) {
      return undefined;
    }
    return parsed;
  }

  function buildFilters(): ScreenerFilters {
    return {
      symbol_query: draft.symbol_query || undefined,
      sector: draft.sector || undefined,
      asset_type: draft.asset_type || undefined,
      watchlist_id: draft.watchlist_id || undefined,
      tag: draft.tag || undefined,
      price_min: parseNumber(draft.price_min),
      price_max: parseNumber(draft.price_max),
      market_cap_min: parseNumber(draft.market_cap_min),
      market_cap_max: parseNumber(draft.market_cap_max),
      change_percent_min: parseNumber(draft.change_percent_min),
      change_percent_max: parseNumber(draft.change_percent_max),
      volume_min: parseNumber(draft.volume_min),
      volume_max: parseNumber(draft.volume_max),
      sort_by: draft.sort_by,
      sort_direction: draft.sort_direction,
      limit: parseNumber(draft.limit)
    };
  }

  function applyCriteria(criteria: Record<string, unknown>) {
    setDraft({
      symbol_query: String(criteria.symbol_query ?? ""),
      sector: String(criteria.sector ?? ""),
      asset_type: String(criteria.asset_type ?? ""),
      watchlist_id: String(criteria.watchlist_id ?? ""),
      tag: String(criteria.tag ?? ""),
      price_min: criteria.price_min ? String(criteria.price_min) : "",
      price_max: criteria.price_max ? String(criteria.price_max) : "",
      market_cap_min: criteria.market_cap_min ? String(criteria.market_cap_min) : "",
      market_cap_max: criteria.market_cap_max ? String(criteria.market_cap_max) : "",
      change_percent_min: criteria.change_percent_min ? String(criteria.change_percent_min) : "",
      change_percent_max: criteria.change_percent_max ? String(criteria.change_percent_max) : "",
      volume_min: criteria.volume_min ? String(criteria.volume_min) : "",
      volume_max: criteria.volume_max ? String(criteria.volume_max) : "",
      sort_by: (criteria.sort_by as FilterDraft["sort_by"]) || "symbol",
      sort_direction: (criteria.sort_direction as FilterDraft["sort_direction"]) || "asc",
      limit: criteria.limit ? String(criteria.limit) : "150"
    });
  }

  async function onRunScreener() {
    setIsRunning(true);
    try {
      const nextResults = await runScreener(buildFilters());
      setResults(nextResults);
      setError(null);
      setMessage(`Run completed: ${nextResults.length} matches.`);
    } catch {
      setError("Unable to run screener.");
    } finally {
      setIsRunning(false);
    }
  }

  async function onSaveScreen() {
    const name = saveName.trim();
    if (!name) {
      setError("Provide a name before saving the screen.");
      return;
    }

    setIsRunning(true);
    try {
      const saved = await createSavedScreen({ name, criteria: buildFilters() });
      setSavedScreens((current) => [saved, ...current]);
      setSaveName("");
      setError(null);
      setMessage(`Saved screen "${saved.name}".`);
    } catch {
      setError("Unable to save screener view.");
    } finally {
      setIsRunning(false);
    }
  }

  async function onRunSavedScreen(screen: SavedScreen) {
    setIsRunning(true);
    try {
      applyCriteria(screen.criteria);
      const nextResults = await runSavedScreen(screen.id);
      setResults(nextResults);
      setError(null);
      setMessage(`Loaded saved screen "${screen.name}" (${nextResults.length} results).`);
    } catch {
      setError("Unable to run saved screen.");
    } finally {
      setIsRunning(false);
    }
  }

  async function onDeleteSavedScreen(screenId: string) {
    setIsRunning(true);
    try {
      await deleteSavedScreen(screenId);
      setSavedScreens((current) => current.filter((item) => item.id !== screenId));
      setError(null);
      setMessage("Saved screen removed.");
    } catch {
      setError("Unable to delete saved screen.");
    } finally {
      setIsRunning(false);
    }
  }

  function setSort(sortBy: FilterDraft["sort_by"]) {
    setDraft((current) => {
      const nextDirection: FilterDraft["sort_direction"] =
        current.sort_by === sortBy && current.sort_direction === "asc" ? "desc" : "asc";
      return {
        ...current,
        sort_by: sortBy,
        sort_direction: nextDirection
      };
    });
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.16em] text-textSecondary">Phase 7</p>
          <h2 className="text-2xl font-semibold text-textPrimary">Screener</h2>
          <p className="text-xs text-textSecondary">
            Shortcuts: <kbd>/</kbd> focus symbol, <kbd>Cmd/Ctrl</kbd>+<kbd>Enter</kbd> run, <kbd>Cmd/Ctrl</kbd>+<kbd>S</kbd> save.
          </p>
        </div>
      </header>

      {error ? <StateNotice tone="error" title={error} /> : null}
      {message ? <StateNotice title={message} /> : null}

      <div className="grid gap-6 xl:grid-cols-[2fr,1fr]">
        <section className="panel">
          <div className="panel-header">
            <h3 className="text-sm font-semibold text-textPrimary">Filters</h3>
          </div>
          <div className="panel-body grid gap-2 md:grid-cols-4">
            <input
              ref={symbolInputRef}
              value={draft.symbol_query}
              onChange={(event) => setDraft((current) => ({ ...current, symbol_query: event.target.value }))}
              placeholder="Symbol or company"
              className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
            />
            <select
              value={draft.asset_type}
              onChange={(event) => setDraft((current) => ({ ...current, asset_type: event.target.value }))}
              className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
            >
              <option value="">All asset types</option>
              <option value="equity">Equity</option>
              <option value="etf">ETF</option>
            </select>
            <select
              value={draft.watchlist_id}
              onChange={(event) => setDraft((current) => ({ ...current, watchlist_id: event.target.value }))}
              className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
            >
              <option value="">All watchlists</option>
              {watchlists.map((watchlist) => (
                <option key={watchlist.id} value={watchlist.id}>
                  {watchlist.name}
                </option>
              ))}
            </select>
            <input
              value={draft.tag}
              onChange={(event) => setDraft((current) => ({ ...current, tag: event.target.value }))}
              placeholder="Tag"
              className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
            />
            <input
              value={draft.price_min}
              onChange={(event) => setDraft((current) => ({ ...current, price_min: event.target.value }))}
              type="number"
              placeholder="Price min"
              className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
            />
            <input
              value={draft.price_max}
              onChange={(event) => setDraft((current) => ({ ...current, price_max: event.target.value }))}
              type="number"
              placeholder="Price max"
              className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
            />
            <input
              value={draft.market_cap_min}
              onChange={(event) => setDraft((current) => ({ ...current, market_cap_min: event.target.value }))}
              type="number"
              placeholder="Market cap min"
              className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
            />
            <input
              value={draft.market_cap_max}
              onChange={(event) => setDraft((current) => ({ ...current, market_cap_max: event.target.value }))}
              type="number"
              placeholder="Market cap max"
              className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
            />
            <input
              value={draft.change_percent_min}
              onChange={(event) => setDraft((current) => ({ ...current, change_percent_min: event.target.value }))}
              type="number"
              placeholder="Change % min"
              className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
            />
            <input
              value={draft.change_percent_max}
              onChange={(event) => setDraft((current) => ({ ...current, change_percent_max: event.target.value }))}
              type="number"
              placeholder="Change % max"
              className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
            />
            <input
              value={draft.volume_min}
              onChange={(event) => setDraft((current) => ({ ...current, volume_min: event.target.value }))}
              type="number"
              placeholder="Volume min"
              className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
            />
            <input
              value={draft.volume_max}
              onChange={(event) => setDraft((current) => ({ ...current, volume_max: event.target.value }))}
              type="number"
              placeholder="Volume max"
              className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
            />
            <select
              value={draft.sector}
              onChange={(event) => setDraft((current) => ({ ...current, sector: event.target.value }))}
              className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
            >
              <option value="">All sectors</option>
              {sectors.map((sector) => (
                <option key={sector} value={sector}>
                  {sector}
                </option>
              ))}
            </select>
            <select
              value={draft.sort_by}
              onChange={(event) =>
                setDraft((current) => ({
                  ...current,
                  sort_by: event.target.value as FilterDraft["sort_by"]
                }))
              }
              className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
            >
              <option value="symbol">Sort by Symbol</option>
              <option value="name">Sort by Name</option>
              <option value="price">Sort by Price</option>
              <option value="change_percent">Sort by Change %</option>
              <option value="market_cap">Sort by Market Cap</option>
              <option value="volume">Sort by Volume</option>
            </select>
            <select
              value={draft.sort_direction}
              onChange={(event) =>
                setDraft((current) => ({
                  ...current,
                  sort_direction: event.target.value as FilterDraft["sort_direction"]
                }))
              }
              className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
            >
              <option value="asc">Ascending</option>
              <option value="desc">Descending</option>
            </select>
            <input
              value={draft.limit}
              onChange={(event) => setDraft((current) => ({ ...current, limit: event.target.value }))}
              type="number"
              placeholder="Limit"
              className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
            />
            <div className="flex gap-2 md:col-span-4">
              <button
                type="button"
                onClick={() => {
                  void onRunScreener();
                }}
                className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-[#06121e]"
                disabled={isRunning}
              >
                {isRunning ? "Running..." : "Run Screen"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setDraft(defaultDraft);
                }}
                className="rounded-md border border-border px-3 py-2 text-sm text-textSecondary"
                disabled={isRunning}
              >
                Clear
              </button>
            </div>
          </div>
        </section>

        <section className="panel">
          <div className="panel-header">
            <h3 className="text-sm font-semibold text-textPrimary">Saved Screens</h3>
          </div>
          <div className="panel-body space-y-3">
            <div className="flex gap-2">
              <input
                value={saveName}
                onChange={(event) => setSaveName(event.target.value)}
                placeholder="Screen name"
                className="w-full rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
              />
              <button
                type="button"
                onClick={() => {
                  void onSaveScreen();
                }}
                className="rounded-md border border-border px-3 py-2 text-sm text-textSecondary"
                disabled={isRunning}
              >
                Save
              </button>
            </div>
            {savedScreens.length === 0 ? (
              <StateNotice title="No saved screens yet." detail="Run a filter set and save it for reuse." />
            ) : (
              <ul className="space-y-2">
                {savedScreens.map((screen) => (
                  <li key={screen.id} className="rounded-md border border-border px-3 py-2">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-sm text-textPrimary">{screen.name}</p>
                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={() => {
                            void onRunSavedScreen(screen);
                          }}
                          className="rounded border border-border px-2 py-1 text-xs text-textSecondary"
                          disabled={isRunning}
                        >
                          Run
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            void onDeleteSavedScreen(screen.id);
                          }}
                          className="rounded border border-danger/40 px-2 py-1 text-xs text-danger"
                          disabled={isRunning}
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>
      </div>

      <section className="panel">
        <div className="panel-header">
          <h3 className="text-sm font-semibold text-textPrimary">Results</h3>
        </div>
        <div className="panel-body overflow-auto">
          {results.length === 0 ? (
            <StateNotice
              tone="warning"
              title="No matches for current criteria."
              detail="Adjust filters, widen ranges, or remove watchlist constraints."
            />
          ) : (
            <table className="min-w-full text-left">
              <thead className="bg-panelMuted text-xs text-textSecondary">
                <tr>
                  <th className="table-cell">Symbol</th>
                  <th className="table-cell">Name</th>
                  <th className="table-cell">Asset</th>
                  <th className="table-cell">Sector</th>
                  <th className="table-cell">
                    <button type="button" onClick={() => setSort("price")} className="hover:text-textPrimary">
                      Price
                    </button>
                  </th>
                  <th className="table-cell">
                    <button
                      type="button"
                      onClick={() => setSort("change_percent")}
                      className="hover:text-textPrimary"
                    >
                      Change %
                    </button>
                  </th>
                  <th className="table-cell">
                    <button
                      type="button"
                      onClick={() => setSort("market_cap")}
                      className="hover:text-textPrimary"
                    >
                      Market Cap
                    </button>
                  </th>
                  <th className="table-cell">
                    <button type="button" onClick={() => setSort("volume")} className="hover:text-textPrimary">
                      Volume
                    </button>
                  </th>
                </tr>
              </thead>
              <tbody>
                {results.map((row) => (
                  <tr key={row.symbol} className="border-t border-border hover:bg-panelMuted/40">
                    <td className="table-cell font-medium text-textPrimary">
                      <Link href={`/security/${row.symbol}`}>{row.symbol}</Link>
                    </td>
                    <td className="table-cell text-textPrimary">{row.name}</td>
                    <td className="table-cell text-textSecondary">{row.asset_type}</td>
                    <td className="table-cell text-textSecondary">{row.sector ?? "-"}</td>
                    <td className="table-cell text-textPrimary">{formatCurrency(row.price)}</td>
                    <td className={`table-cell ${row.change_percent >= 0 ? "text-success" : "text-danger"}`}>
                      {formatPercent(row.change_percent)}
                    </td>
                    <td className="table-cell text-textSecondary">{formatCompact(row.market_cap)}</td>
                    <td className="table-cell text-textSecondary">{formatCompact(row.volume)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </section>
    </div>
  );
}
