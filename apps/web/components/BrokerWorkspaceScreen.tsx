"use client";

import { useState } from "react";

import {
  createBrokerOrderEvent,
  getBrokerAccounts,
  getBrokerCapabilities,
  getBrokerOrderEvents,
  getBrokerReconciliation,
  getJournalEntries,
  getReconciliationExceptions,
  previewBrokerOrder,
  resolveReconciliationException,
  syncBroker
} from "@/lib/api";
import { formatCurrency, formatDateTime } from "@/lib/format";
import type {
  BrokerAccount,
  BrokerCapabilityStatus,
  BrokerOrderEvent,
  BrokerOrderPreview,
  BrokerReconciliation,
  ReconciliationException,
  TradeJournalEntry
} from "@/lib/types";
import { StateNotice } from "@/components/StateNotice";

interface BrokerWorkspaceScreenProps {
  initialAccounts: BrokerAccount[];
  initialReconciliation: BrokerReconciliation;
  initialCapabilities: BrokerCapabilityStatus;
  initialExceptions: ReconciliationException[];
  initialOrderEvents: BrokerOrderEvent[];
  initialJournalEntries: TradeJournalEntry[];
}

interface OrderDraft {
  symbol: string;
  side: "buy" | "sell";
  orderType: "market" | "limit";
  quantity: string;
  limitPrice: string;
}

const defaultOrderDraft: OrderDraft = {
  symbol: "AAPL",
  side: "buy",
  orderType: "market",
  quantity: "10",
  limitPrice: ""
};

export function BrokerWorkspaceScreen({
  initialAccounts,
  initialReconciliation,
  initialCapabilities,
  initialExceptions,
  initialOrderEvents,
  initialJournalEntries
}: BrokerWorkspaceScreenProps) {
  const [accounts, setAccounts] = useState(initialAccounts);
  const [reconciliation, setReconciliation] = useState(initialReconciliation);
  const [capabilityStatus, setCapabilityStatus] = useState(initialCapabilities);
  const [exceptions, setExceptions] = useState(initialExceptions);
  const [orderEvents, setOrderEvents] = useState(initialOrderEvents);
  const [journalEntries, setJournalEntries] = useState(initialJournalEntries);
  const [orderDraft, setOrderDraft] = useState<OrderDraft>(defaultOrderDraft);
  const [preview, setPreview] = useState<BrokerOrderPreview | null>(null);
  const [isSyncing, setIsSyncing] = useState(false);
  const [isPreviewing, setIsPreviewing] = useState(false);
  const [isRecordingFill, setIsRecordingFill] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function refreshBrokerData() {
    const [
      nextCapabilities,
      nextAccounts,
      nextReconciliation,
      nextExceptions,
      nextOrderEvents,
      nextJournalEntries
    ] = await Promise.all([
      getBrokerCapabilities(),
      getBrokerAccounts(),
      getBrokerReconciliation(),
      getReconciliationExceptions("open"),
      getBrokerOrderEvents({ limit: 20 }),
      getJournalEntries({ limit: 20 })
    ]);

    setCapabilityStatus(nextCapabilities);
    setAccounts(nextAccounts);
    setReconciliation(nextReconciliation);
    setExceptions(nextExceptions);
    setOrderEvents(nextOrderEvents);
    setJournalEntries(nextJournalEntries);
  }

  async function onSync() {
    setIsSyncing(true);
    try {
      const result = await syncBroker();
      await refreshBrokerData();
      setError(null);
      setMessage(
        `${result.message} Accounts: ${result.fetched_accounts}, positions: ${result.fetched_positions}.`
      );
    } catch {
      setError("Broker sync failed.");
    } finally {
      setIsSyncing(false);
    }
  }

  async function onPreviewOrder() {
    const quantity = Number(orderDraft.quantity);
    if (!Number.isFinite(quantity) || quantity <= 0) {
      setError("Order quantity must be a positive number.");
      return;
    }

    const limitPrice =
      orderDraft.orderType === "limit" && orderDraft.limitPrice.trim()
        ? Number(orderDraft.limitPrice)
        : undefined;

    setIsPreviewing(true);
    try {
      const response = await previewBrokerOrder({
        symbol: orderDraft.symbol.trim().toUpperCase(),
        side: orderDraft.side,
        order_type: orderDraft.orderType,
        quantity,
        limit_price: limitPrice
      });
      setPreview(response);
      setError(null);
    } catch {
      setError("Unable to preview broker order.");
    } finally {
      setIsPreviewing(false);
    }
  }

  async function onRecordFill() {
    const quantity = Number(orderDraft.quantity);
    if (!Number.isFinite(quantity) || quantity <= 0) {
      setError("Order quantity must be a positive number.");
      return;
    }

    setIsRecordingFill(true);
    try {
      await createBrokerOrderEvent({
        broker_account_id: accounts[0]?.id ?? null,
        external_order_id: `manual-${Date.now()}`,
        symbol: orderDraft.symbol.trim().toUpperCase(),
        side: orderDraft.side,
        order_type: orderDraft.orderType,
        status: "filled",
        quantity,
        limit_price:
          orderDraft.orderType === "limit" && orderDraft.limitPrice.trim()
            ? Number(orderDraft.limitPrice)
            : null,
        filled_quantity: quantity,
        avg_fill_price: preview?.reference_price ?? null,
        event_payload: { source: "manual_ui" },
        create_journal_entry: true
      });
      await refreshBrokerData();
      setError(null);
      setMessage("Broker fill event recorded and journal entry created.");
    } catch {
      setError("Unable to record broker fill event.");
    } finally {
      setIsRecordingFill(false);
    }
  }

  async function onResolveException(exceptionId: string) {
    try {
      await resolveReconciliationException(exceptionId, "Resolved manually from broker workspace.");
      await refreshBrokerData();
      setError(null);
      setMessage("Reconciliation exception resolved.");
    } catch {
      setError("Unable to resolve reconciliation exception.");
    }
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.16em] text-textSecondary">Phase 9</p>
          <h2 className="text-2xl font-semibold text-textPrimary">Broker Execution & Reconciliation</h2>
          <p className="text-xs text-textSecondary">
            Capability-gated execution preview, reconciliation exceptions, and journal linkage.
          </p>
        </div>
        <button
          type="button"
          onClick={() => {
            void onSync();
          }}
          className="ml-auto rounded-md bg-accent px-4 py-2 text-sm font-medium text-[#06121e]"
          disabled={isSyncing}
        >
          {isSyncing ? "Syncing..." : "Run Broker Sync"}
        </button>
      </header>

      {error ? <StateNotice tone="error" title={error} /> : null}
      {message ? <StateNotice title={message} /> : null}

      <section className="grid gap-6 xl:grid-cols-[1.3fr,1fr]">
        <div className="panel">
          <div className="panel-header">
            <h3 className="text-sm font-semibold text-textPrimary">Broker Capability Status</h3>
          </div>
          <div className="panel-body grid gap-3 md:grid-cols-2">
            <div className="rounded-md border border-border px-3 py-2 text-xs">
              <p className="text-textSecondary">Provider</p>
              <p className="text-textPrimary">{capabilityStatus.capabilities.provider}</p>
            </div>
            <div className="rounded-md border border-border px-3 py-2 text-xs">
              <p className="text-textSecondary">Session</p>
              <p className={capabilityStatus.session.connected ? "text-success" : "text-danger"}>
                {capabilityStatus.session.connected ? "Connected" : "Disconnected"}
              </p>
              <p className="text-textSecondary">{capabilityStatus.session.auth_state}</p>
            </div>
            <div className="rounded-md border border-border px-3 py-2 text-xs">
              <p className="text-textSecondary">Order Submission</p>
              <p
                className={
                  capabilityStatus.capabilities.can_submit_orders ? "text-success" : "text-warning"
                }
              >
                {capabilityStatus.capabilities.can_submit_orders ? "Enabled" : "Disabled"}
              </p>
            </div>
            <div className="rounded-md border border-border px-3 py-2 text-xs">
              <p className="text-textSecondary">Restrictions</p>
              <p className="text-textPrimary">
                {capabilityStatus.capabilities.restrictions.length > 0
                  ? capabilityStatus.capabilities.restrictions.join(" ")
                  : "None"}
              </p>
            </div>
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <h3 className="text-sm font-semibold text-textPrimary">Order Preview</h3>
          </div>
          <div className="panel-body space-y-2">
            <div className="grid grid-cols-2 gap-2">
              <input
                value={orderDraft.symbol}
                onChange={(event) =>
                  setOrderDraft((current) => ({ ...current, symbol: event.target.value }))
                }
                placeholder="Symbol"
                className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
              />
              <select
                value={orderDraft.side}
                onChange={(event) =>
                  setOrderDraft((current) => ({
                    ...current,
                    side: event.target.value as "buy" | "sell"
                  }))
                }
                className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
              >
                <option value="buy">Buy</option>
                <option value="sell">Sell</option>
              </select>
              <select
                value={orderDraft.orderType}
                onChange={(event) =>
                  setOrderDraft((current) => ({
                    ...current,
                    orderType: event.target.value as "market" | "limit"
                  }))
                }
                className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
              >
                <option value="market">Market</option>
                <option value="limit">Limit</option>
              </select>
              <input
                value={orderDraft.quantity}
                onChange={(event) =>
                  setOrderDraft((current) => ({ ...current, quantity: event.target.value }))
                }
                type="number"
                min="0"
                step="0.0001"
                placeholder="Quantity"
                className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
              />
              {orderDraft.orderType === "limit" ? (
                <input
                  value={orderDraft.limitPrice}
                  onChange={(event) =>
                    setOrderDraft((current) => ({ ...current, limitPrice: event.target.value }))
                  }
                  type="number"
                  min="0"
                  step="0.0001"
                  placeholder="Limit price"
                  className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary col-span-2"
                />
              ) : null}
            </div>

            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => {
                  void onPreviewOrder();
                }}
                className="rounded-md border border-border px-3 py-2 text-sm text-textSecondary hover:text-textPrimary"
                disabled={isPreviewing}
              >
                {isPreviewing ? "Previewing..." : "Preview"}
              </button>
              <button
                type="button"
                onClick={() => {
                  void onRecordFill();
                }}
                className="rounded-md border border-border px-3 py-2 text-sm text-textSecondary hover:text-textPrimary"
                disabled={isRecordingFill}
              >
                {isRecordingFill ? "Recording..." : "Record Fill Event"}
              </button>
            </div>

            {preview ? (
              <div className="rounded-md border border-border px-3 py-2 text-xs text-textSecondary">
                <p className="text-textPrimary">
                  {preview.symbol} {preview.side.toUpperCase()} {preview.quantity.toFixed(4)} @{" "}
                  {formatCurrency(preview.reference_price)}
                </p>
                <p>Notional {formatCurrency(preview.estimated_notional)}</p>
                <p>Fees {formatCurrency(preview.estimated_fees)}</p>
                <p>Cash impact {formatCurrency(preview.estimated_total_cash)}</p>
                {preview.restrictions.length > 0 ? (
                  <p className="text-warning">{preview.restrictions.join(" ")}</p>
                ) : null}
              </div>
            ) : (
              <StateNotice title="No preview yet." />
            )}
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-5">
        <Metric label="Local symbols" value={String(reconciliation.summary.local_symbol_count)} />
        <Metric label="Broker symbols" value={String(reconciliation.summary.broker_symbol_count)} />
        <Metric label="Only local" value={String(reconciliation.summary.only_local_count)} />
        <Metric label="Only broker" value={String(reconciliation.summary.only_broker_count)} />
        <Metric label="Open exceptions" value={String(reconciliation.open_exception_count)} />
      </section>

      <section className="panel">
        <div className="panel-header">
          <h3 className="text-sm font-semibold text-textPrimary">Reconciliation Exceptions</h3>
        </div>
        <div className="panel-body">
          {exceptions.length === 0 ? (
            <StateNotice title="No open reconciliation exceptions." />
          ) : (
            <ul className="space-y-2">
              {exceptions.map((item) => (
                <li key={item.id} className="rounded-md border border-border px-3 py-2 text-xs">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm text-textPrimary">
                      {item.symbol} · {item.issue_type}
                    </p>
                    <button
                      type="button"
                      onClick={() => {
                        void onResolveException(item.id);
                      }}
                      className="rounded border border-border px-2 py-1 text-xs text-textSecondary"
                    >
                      Resolve
                    </button>
                  </div>
                  <p className="text-textSecondary">
                    Severity {item.severity} · Last seen {formatDateTime(item.last_seen_at)}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h3 className="text-sm font-semibold text-textPrimary">Broker Accounts</h3>
          <p className="text-xs text-textSecondary">Latest synced snapshots</p>
        </div>
        <div className="panel-body space-y-4">
          {accounts.length === 0 ? (
            <StateNotice
              title="No broker accounts synced yet."
              detail="Run broker sync to create local snapshots."
            />
          ) : (
            accounts.map((account) => (
              <article key={account.id} className="rounded-lg border border-border p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <p className="text-sm font-medium text-textPrimary">{account.account_name}</p>
                    <p className="text-xs text-textSecondary">
                      {account.provider} · {account.account_type} · {account.external_account_id}
                    </p>
                  </div>
                  <div className="text-right text-xs text-textSecondary">
                    <p>{account.position_count} positions</p>
                    <p>{formatCurrency(account.total_market_value)}</p>
                    <p>
                      Synced {account.last_synced_at ? formatDateTime(account.last_synced_at) : "not yet"}
                    </p>
                  </div>
                </div>
              </article>
            ))
          )}
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-2">
        <div className="panel">
          <div className="panel-header">
            <h3 className="text-sm font-semibold text-textPrimary">Recent Broker Order Events</h3>
          </div>
          <div className="panel-body">
            {orderEvents.length === 0 ? (
              <StateNotice title="No broker events recorded." />
            ) : (
              <ul className="space-y-2">
                {orderEvents.map((event) => (
                  <li key={event.id} className="rounded-md border border-border px-3 py-2 text-xs">
                    <p className="text-sm text-textPrimary">
                      {event.symbol} {event.side.toUpperCase()} · {event.status}
                    </p>
                    <p className="text-textSecondary">
                      {event.order_type} · qty {event.quantity.toFixed(4)} · ext {event.external_order_id}
                    </p>
                    <p className="text-textSecondary">{formatDateTime(event.submitted_at)}</p>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <h3 className="text-sm font-semibold text-textPrimary">Trade Journal (Linked)</h3>
          </div>
          <div className="panel-body">
            {journalEntries.length === 0 ? (
              <StateNotice title="No journal entries linked yet." />
            ) : (
              <ul className="space-y-2">
                {journalEntries.map((entry) => (
                  <li key={entry.id} className="rounded-md border border-border px-3 py-2 text-xs">
                    <p className="text-sm text-textPrimary">{entry.title}</p>
                    <p className="text-textSecondary">{entry.body}</p>
                    <p className="text-textSecondary">
                      {entry.symbol ?? "GLOBAL"} · {entry.entry_type} · {formatDateTime(entry.created_at)}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}

interface MetricProps {
  label: string;
  value: string;
}

function Metric({ label, value }: MetricProps) {
  return (
    <div className="panel px-4 py-3">
      <p className="kpi-label">{label}</p>
      <p className="kpi-value">{value}</p>
    </div>
  );
}
