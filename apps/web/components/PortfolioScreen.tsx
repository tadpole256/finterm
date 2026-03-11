"use client";

import { useState } from "react";

import {
  createPortfolioTransaction,
  deletePortfolioTransaction,
  getPortfolioOverview
} from "@/lib/api";
import { formatCurrency, formatDateTime } from "@/lib/format";
import type {
  PortfolioOverviewPayload,
  PortfolioTransactionSide
} from "@/lib/types";

interface PortfolioScreenProps {
  initialOverview: PortfolioOverviewPayload;
}

interface TransactionDraft {
  symbol: string;
  side: PortfolioTransactionSide;
  quantity: string;
  price: string;
  fees: string;
  notes: string;
}

const defaultDraft: TransactionDraft = {
  symbol: "",
  side: "buy",
  quantity: "",
  price: "",
  fees: "0",
  notes: ""
};

export function PortfolioScreen({ initialOverview }: PortfolioScreenProps) {
  const [overview, setOverview] = useState(initialOverview);
  const [draft, setDraft] = useState<TransactionDraft>(defaultDraft);
  const [isSaving, setIsSaving] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refreshOverview() {
    setIsRefreshing(true);
    try {
      const next = await getPortfolioOverview(overview.portfolio.id);
      setOverview(next);
      setError(null);
    } catch {
      setError("Unable to refresh portfolio snapshot.");
    } finally {
      setIsRefreshing(false);
    }
  }

  async function onSubmitTransaction() {
    const symbol = draft.symbol.trim().toUpperCase();
    const quantity = Number(draft.quantity);
    const price = Number(draft.price);
    const fees = Number(draft.fees || 0);

    if (!symbol || !Number.isFinite(quantity) || quantity <= 0 || !Number.isFinite(price) || price <= 0) {
      setError("Provide symbol, quantity, and price.");
      return;
    }

    setIsSaving(true);
    try {
      await createPortfolioTransaction({
        portfolio_id: overview.portfolio.id,
        symbol,
        side: draft.side,
        quantity,
        price,
        fees,
        notes: draft.notes.trim() || undefined
      });
      setDraft(defaultDraft);
      setError(null);
      await refreshOverview();
    } catch {
      setError("Unable to create transaction.");
    } finally {
      setIsSaving(false);
    }
  }

  async function onDeleteTransaction(transactionId: string) {
    try {
      await deletePortfolioTransaction(transactionId);
      setError(null);
      await refreshOverview();
    } catch {
      setError("Unable to delete transaction.");
    }
  }

  const totalPnlClass = overview.summary.total_pnl >= 0 ? "text-success" : "text-danger";

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.16em] text-textSecondary">Portfolio</p>
          <h2 className="text-2xl font-semibold text-textPrimary">{overview.portfolio.name}</h2>
          <p className="text-xs text-textSecondary">
            Snapshot {formatDateTime(overview.as_of)} · {overview.portfolio.base_currency}
          </p>
        </div>
        <button
          type="button"
          onClick={() => {
            void refreshOverview();
          }}
          className="ml-auto rounded-md border border-border px-3 py-2 text-xs text-textSecondary hover:text-textPrimary"
        >
          {isRefreshing ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-6">
        <SummaryCard label="Market Value" value={formatCurrency(overview.summary.market_value)} />
        <SummaryCard label="Cost Basis" value={formatCurrency(overview.summary.cost_basis)} />
        <SummaryCard
          label="Unrealized P&L"
          value={formatCurrency(overview.summary.unrealized_pnl)}
          valueClass={overview.summary.unrealized_pnl >= 0 ? "text-success" : "text-danger"}
        />
        <SummaryCard
          label="Realized P&L"
          value={formatCurrency(overview.summary.realized_pnl)}
          valueClass={overview.summary.realized_pnl >= 0 ? "text-success" : "text-danger"}
        />
        <SummaryCard label="Total P&L" value={formatCurrency(overview.summary.total_pnl)} valueClass={totalPnlClass} />
        <SummaryCard label="Positions" value={String(overview.summary.position_count)} />
      </div>

      {error ? (
        <div className="rounded-md border border-danger/40 bg-danger/10 px-3 py-2 text-sm text-danger">
          {error}
        </div>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[2fr,1fr]">
        <section className="panel">
          <div className="panel-header">
            <h3 className="text-sm font-semibold text-textPrimary">Holdings</h3>
            <p className="text-xs text-textSecondary">Linked to watchlists and research artifacts</p>
          </div>
          <div className="panel-body overflow-auto">
            <table className="min-w-full">
              <thead className="text-left text-xs text-textSecondary">
                <tr>
                  <th className="table-cell">Symbol</th>
                  <th className="table-cell">Quantity</th>
                  <th className="table-cell">Avg Cost</th>
                  <th className="table-cell">Last</th>
                  <th className="table-cell">Market Value</th>
                  <th className="table-cell">Unrealized</th>
                  <th className="table-cell">Realized</th>
                  <th className="table-cell">Research</th>
                  <th className="table-cell">Watchlists</th>
                </tr>
              </thead>
              <tbody>
                {overview.holdings.map((holding) => (
                  <tr key={holding.instrument_id} className="border-t border-border">
                    <td className="table-cell">
                      <p className="font-medium text-textPrimary">{holding.symbol}</p>
                      <p className="text-xs text-textSecondary">{holding.name}</p>
                    </td>
                    <td className="table-cell text-textPrimary">{holding.quantity.toFixed(4)}</td>
                    <td className="table-cell text-textPrimary">{formatCurrency(holding.avg_cost)}</td>
                    <td className="table-cell text-textPrimary">
                      {holding.last_price !== null ? formatCurrency(holding.last_price) : "N/A"}
                    </td>
                    <td className="table-cell text-textPrimary">
                      {holding.market_value !== null ? formatCurrency(holding.market_value) : "N/A"}
                    </td>
                    <td
                      className={`table-cell ${
                        (holding.unrealized_pnl ?? 0) >= 0 ? "text-success" : "text-danger"
                      }`}
                    >
                      {holding.unrealized_pnl !== null ? formatCurrency(holding.unrealized_pnl) : "N/A"}
                    </td>
                    <td className={`table-cell ${holding.realized_pnl >= 0 ? "text-success" : "text-danger"}`}>
                      {formatCurrency(holding.realized_pnl)}
                    </td>
                    <td className="table-cell text-xs text-textSecondary">
                      {holding.note_count} notes · {holding.active_thesis_count} thesis
                    </td>
                    <td className="table-cell text-xs text-textSecondary">
                      {holding.watchlists.length > 0 ? holding.watchlists.join(", ") : "-"}
                    </td>
                  </tr>
                ))}
                {overview.holdings.length === 0 ? (
                  <tr>
                    <td className="table-cell text-textSecondary" colSpan={9}>
                      No open holdings.
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </section>

        <div className="space-y-6">
          <section className="panel">
            <div className="panel-header">
              <h3 className="text-sm font-semibold text-textPrimary">Sector Exposure</h3>
              <p className="text-xs text-textSecondary">Weight based on current market value</p>
            </div>
            <div className="panel-body space-y-2">
              {overview.exposures.map((item) => (
                <div
                  key={item.sector}
                  className="rounded-md border border-border px-3 py-2 text-xs text-textSecondary"
                >
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-textPrimary">{item.sector}</p>
                    <p>{(item.weight * 100).toFixed(1)}%</p>
                  </div>
                  <p className="mt-1">{formatCurrency(item.market_value)}</p>
                </div>
              ))}
              {overview.exposures.length === 0 ? (
                <p className="text-sm text-textSecondary">No exposure data available.</p>
              ) : null}
            </div>
          </section>

          <section className="panel">
            <div className="panel-header">
              <h3 className="text-sm font-semibold text-textPrimary">Add Transaction</h3>
              <p className="text-xs text-textSecondary">Buy/sell updates recompute positions and P&L</p>
            </div>
            <div className="panel-body space-y-3">
              <div className="grid gap-2 sm:grid-cols-2">
                <input
                  value={draft.symbol}
                  onChange={(event) => setDraft((prev) => ({ ...prev, symbol: event.target.value }))}
                  placeholder="Symbol"
                  className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
                />
                <select
                  value={draft.side}
                  onChange={(event) =>
                    setDraft((prev) => ({ ...prev, side: event.target.value as PortfolioTransactionSide }))
                  }
                  className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
                >
                  <option value="buy">Buy</option>
                  <option value="sell">Sell</option>
                </select>
                <input
                  value={draft.quantity}
                  onChange={(event) => setDraft((prev) => ({ ...prev, quantity: event.target.value }))}
                  placeholder="Quantity"
                  type="number"
                  min="0"
                  step="0.0001"
                  className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
                />
                <input
                  value={draft.price}
                  onChange={(event) => setDraft((prev) => ({ ...prev, price: event.target.value }))}
                  placeholder="Price"
                  type="number"
                  min="0"
                  step="0.0001"
                  className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
                />
                <input
                  value={draft.fees}
                  onChange={(event) => setDraft((prev) => ({ ...prev, fees: event.target.value }))}
                  placeholder="Fees"
                  type="number"
                  min="0"
                  step="0.01"
                  className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
                />
                <input
                  value={draft.notes}
                  onChange={(event) => setDraft((prev) => ({ ...prev, notes: event.target.value }))}
                  placeholder="Notes"
                  className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
                />
              </div>
              <button
                type="button"
                onClick={() => {
                  void onSubmitTransaction();
                }}
                className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-[#06121e]"
                disabled={isSaving}
              >
                {isSaving ? "Saving..." : "Submit Transaction"}
              </button>
            </div>
          </section>
        </div>
      </div>

      <section className="panel">
        <div className="panel-header">
          <h3 className="text-sm font-semibold text-textPrimary">Recent Transactions</h3>
          <p className="text-xs text-textSecondary">Most recent executions in this portfolio</p>
        </div>
        <div className="panel-body overflow-auto">
          <table className="min-w-full">
            <thead className="text-left text-xs text-textSecondary">
              <tr>
                <th className="table-cell">Date</th>
                <th className="table-cell">Symbol</th>
                <th className="table-cell">Side</th>
                <th className="table-cell">Quantity</th>
                <th className="table-cell">Price</th>
                <th className="table-cell">Notional</th>
                <th className="table-cell">Fees</th>
                <th className="table-cell">Notes</th>
                <th className="table-cell">Actions</th>
              </tr>
            </thead>
            <tbody>
              {overview.transactions.map((transaction) => (
                <tr key={transaction.id} className="border-t border-border">
                  <td className="table-cell text-textSecondary">{formatDateTime(transaction.trade_date)}</td>
                  <td className="table-cell text-textPrimary">{transaction.symbol}</td>
                  <td
                    className={`table-cell uppercase ${
                      transaction.side === "buy" ? "text-success" : "text-danger"
                    }`}
                  >
                    {transaction.side}
                  </td>
                  <td className="table-cell text-textPrimary">{transaction.quantity.toFixed(4)}</td>
                  <td className="table-cell text-textPrimary">{formatCurrency(transaction.price)}</td>
                  <td className="table-cell text-textPrimary">{formatCurrency(transaction.notional)}</td>
                  <td className="table-cell text-textPrimary">{formatCurrency(transaction.fees)}</td>
                  <td className="table-cell text-xs text-textSecondary">{transaction.notes ?? "-"}</td>
                  <td className="table-cell">
                    <button
                      type="button"
                      onClick={() => {
                        void onDeleteTransaction(transaction.id);
                      }}
                      className="rounded border border-danger/40 px-2 py-1 text-xs text-danger"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
              {overview.transactions.length === 0 ? (
                <tr>
                  <td className="table-cell text-textSecondary" colSpan={9}>
                    No transactions recorded.
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

interface SummaryCardProps {
  label: string;
  value: string;
  valueClass?: string;
}

function SummaryCard({ label, value, valueClass }: SummaryCardProps) {
  return (
    <div className="panel p-4">
      <p className="kpi-label">{label}</p>
      <p className={`kpi-value ${valueClass ?? ""}`}>{value}</p>
    </div>
  );
}
