"use client";

import { useMemo, useState } from "react";

import {
  addWatchlistItem,
  createWatchlist,
  removeWatchlistItem,
  reorderWatchlistItems,
  updateWatchlistLayout
} from "@/lib/api";
import { formatCurrency, formatPercent } from "@/lib/format";
import type { Watchlist, WatchlistLayoutState } from "@/lib/types";

interface WatchlistsScreenProps {
  initialWatchlists: Watchlist[];
  initialLayout: WatchlistLayoutState;
}

const USER_ID = "00000000-0000-0000-0000-000000000001";

export function WatchlistsScreen({
  initialWatchlists,
  initialLayout
}: WatchlistsScreenProps) {
  const [watchlists, setWatchlists] = useState(initialWatchlists);
  const [layout, setLayout] = useState(initialLayout);
  const [newWatchlistName, setNewWatchlistName] = useState("");
  const [symbolInput, setSymbolInput] = useState("");

  const tags = useMemo(
    () =>
      Array.from(
        new Set(
          watchlists
            .flatMap((watchlist) => watchlist.items)
            .flatMap((item) => item.tags)
            .filter(Boolean)
        )
      ),
    [watchlists]
  );

  async function persistLayout(next: WatchlistLayoutState) {
    setLayout(next);
    await updateWatchlistLayout(USER_ID, next);
  }

  async function onCreateWatchlist() {
    if (!newWatchlistName.trim()) {
      return;
    }
    const created = await createWatchlist(newWatchlistName.trim(), null);
    setWatchlists((prev) => [...prev, created]);
    setNewWatchlistName("");
  }

  async function onAddSymbol(watchlistId: string) {
    if (!symbolInput.trim()) {
      return;
    }
    const updated = await addWatchlistItem(watchlistId, symbolInput.trim().toUpperCase(), []);
    setWatchlists((prev) => prev.map((watchlist) => (watchlist.id === watchlistId ? updated : watchlist)));
    setSymbolInput("");
  }

  async function onRemoveSymbol(watchlistId: string, itemId: string) {
    await removeWatchlistItem(watchlistId, itemId);
    setWatchlists((prev) =>
      prev.map((watchlist) =>
        watchlist.id === watchlistId
          ? {
              ...watchlist,
              items: watchlist.items.filter((item) => item.id !== itemId)
            }
          : watchlist
      )
    );
  }

  async function onMove(watchlistId: string, index: number, direction: -1 | 1) {
    const watchlist = watchlists.find((item) => item.id === watchlistId);
    if (!watchlist) {
      return;
    }

    const nextIndex = index + direction;
    if (nextIndex < 0 || nextIndex >= watchlist.items.length) {
      return;
    }

    const reordered = [...watchlist.items];
    const [moved] = reordered.splice(index, 1);
    reordered.splice(nextIndex, 0, moved);

    const updated = await reorderWatchlistItems(
      watchlistId,
      reordered.map((item) => item.id)
    );

    setWatchlists((prev) => prev.map((item) => (item.id === watchlistId ? updated : item)));
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.16em] text-textSecondary">Workspace</p>
          <h2 className="text-2xl font-semibold text-textPrimary">Watchlists</h2>
        </div>

        <div className="ml-auto flex flex-wrap gap-3">
          <label className="flex flex-col gap-1 text-xs text-textSecondary">
            Sort
            <select
              className="rounded-md border border-border bg-panel px-2 py-1 text-sm text-textPrimary"
              value={layout.sortBy}
              onChange={(event) => {
                const next = {
                  ...layout,
                  sortBy: event.target.value as WatchlistLayoutState["sortBy"]
                };
                void persistLayout(next);
              }}
            >
              <option value="symbol">Symbol</option>
              <option value="price">Price</option>
              <option value="change">Change %</option>
            </select>
          </label>

          <label className="flex flex-col gap-1 text-xs text-textSecondary">
            Direction
            <select
              className="rounded-md border border-border bg-panel px-2 py-1 text-sm text-textPrimary"
              value={layout.sortDirection}
              onChange={(event) => {
                const next = {
                  ...layout,
                  sortDirection: event.target.value as WatchlistLayoutState["sortDirection"]
                };
                void persistLayout(next);
              }}
            >
              <option value="asc">Ascending</option>
              <option value="desc">Descending</option>
            </select>
          </label>

          <label className="flex flex-col gap-1 text-xs text-textSecondary">
            Tag
            <select
              className="rounded-md border border-border bg-panel px-2 py-1 text-sm text-textPrimary"
              value={layout.filterTag ?? ""}
              onChange={(event) => {
                const value = event.target.value || null;
                const next = {
                  ...layout,
                  filterTag: value
                };
                void persistLayout(next);
              }}
            >
              <option value="">All tags</option>
              {tags.map((tag) => (
                <option key={tag} value={tag}>
                  {tag}
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>

      <div className="panel p-4">
        <div className="flex flex-wrap items-end gap-3">
          <label className="flex-1 text-sm text-textSecondary">
            New watchlist
            <input
              className="mt-1 w-full rounded-md border border-border bg-panelMuted px-3 py-2 text-textPrimary"
              value={newWatchlistName}
              onChange={(event) => setNewWatchlistName(event.target.value)}
              placeholder="Core"
            />
          </label>
          <button
            type="button"
            onClick={() => {
              void onCreateWatchlist();
            }}
            className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-[#06121e]"
          >
            Create
          </button>
        </div>
      </div>

      {watchlists.map((watchlist) => {
        const filtered = watchlist.items
          .filter((item) => (layout.filterTag ? item.tags.includes(layout.filterTag) : true))
          .sort((left, right) => {
            const direction = layout.sortDirection === "asc" ? 1 : -1;
            if (layout.sortBy === "symbol") {
              return left.symbol.localeCompare(right.symbol) * direction;
            }
            if (layout.sortBy === "price") {
              return (left.quote.price - right.quote.price) * direction;
            }
            return (left.quote.change_percent - right.quote.change_percent) * direction;
          });

        return (
          <section className="panel" key={watchlist.id}>
            <div className="panel-header flex items-center justify-between">
              <div>
                <h3 className="text-base font-medium text-textPrimary">{watchlist.name}</h3>
                <p className="text-xs text-textSecondary">{watchlist.description ?? "No description"}</p>
              </div>
              <div className="flex items-center gap-2 text-xs text-textSecondary">
                <input
                  className="rounded-md border border-border bg-panelMuted px-2 py-1 text-sm text-textPrimary"
                  value={symbolInput}
                  onChange={(event) => setSymbolInput(event.target.value)}
                  placeholder="Add symbol"
                />
                <button
                  type="button"
                  className="rounded-md border border-border px-3 py-1 text-textPrimary"
                  onClick={() => {
                    void onAddSymbol(watchlist.id);
                  }}
                >
                  Add
                </button>
              </div>
            </div>
            <div className="panel-body overflow-auto">
              <table className="min-w-full">
                <thead className="text-left text-xs text-textSecondary">
                  <tr>
                    <th className="table-cell">Symbol</th>
                    <th className="table-cell">Price</th>
                    <th className="table-cell">Change</th>
                    <th className="table-cell">Tags</th>
                    <th className="table-cell">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((item, index) => (
                    <tr key={item.id} className="border-t border-border">
                      <td className="table-cell text-textPrimary">{item.symbol}</td>
                      <td className="table-cell text-textPrimary">{formatCurrency(item.quote.price)}</td>
                      <td
                        className={`table-cell ${
                          item.quote.change_percent >= 0 ? "text-success" : "text-danger"
                        }`}
                      >
                        {formatPercent(item.quote.change_percent)}
                      </td>
                      <td className="table-cell text-textSecondary">{item.tags.join(", ") || "-"}</td>
                      <td className="table-cell">
                        <div className="flex gap-1">
                          <button
                            type="button"
                            className="rounded border border-border px-2 py-1 text-xs text-textSecondary"
                            onClick={() => {
                              void onMove(watchlist.id, index, -1);
                            }}
                          >
                            ↑
                          </button>
                          <button
                            type="button"
                            className="rounded border border-border px-2 py-1 text-xs text-textSecondary"
                            onClick={() => {
                              void onMove(watchlist.id, index, 1);
                            }}
                          >
                            ↓
                          </button>
                          <button
                            type="button"
                            className="rounded border border-danger/40 px-2 py-1 text-xs text-danger"
                            onClick={() => {
                              void onRemoveSymbol(watchlist.id, item.id);
                            }}
                          >
                            Remove
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        );
      })}
    </div>
  );
}
