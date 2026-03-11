"use client";

import { useState } from "react";

import { getBrokerAccounts, getBrokerReconciliation, syncBroker } from "@/lib/api";
import { formatCurrency, formatDateTime } from "@/lib/format";
import type { BrokerAccount, BrokerReconciliation } from "@/lib/types";
import { StateNotice } from "@/components/StateNotice";

interface BrokerWorkspaceScreenProps {
  initialAccounts: BrokerAccount[];
  initialReconciliation: BrokerReconciliation;
}

export function BrokerWorkspaceScreen({
  initialAccounts,
  initialReconciliation
}: BrokerWorkspaceScreenProps) {
  const [accounts, setAccounts] = useState(initialAccounts);
  const [reconciliation, setReconciliation] = useState(initialReconciliation);
  const [isSyncing, setIsSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function refreshBrokerData() {
    const [nextAccounts, nextReconciliation] = await Promise.all([
      getBrokerAccounts(),
      getBrokerReconciliation()
    ]);
    setAccounts(nextAccounts);
    setReconciliation(nextReconciliation);
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

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.16em] text-textSecondary">Phase 8</p>
          <h2 className="text-2xl font-semibold text-textPrimary">Broker Reconciliation</h2>
          <p className="text-xs text-textSecondary">
            Read-only broker adapter foundation with position reconciliation.
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

      <section className="grid gap-4 md:grid-cols-5">
        <Metric label="Local symbols" value={String(reconciliation.summary.local_symbol_count)} />
        <Metric label="Broker symbols" value={String(reconciliation.summary.broker_symbol_count)} />
        <Metric label="Only local" value={String(reconciliation.summary.only_local_count)} />
        <Metric label="Only broker" value={String(reconciliation.summary.only_broker_count)} />
        <Metric
          label="Qty mismatches"
          value={String(reconciliation.summary.quantity_mismatch_count)}
        />
      </section>

      <section className="panel">
        <div className="panel-header">
          <h3 className="text-sm font-semibold text-textPrimary">Broker Accounts</h3>
          <p className="text-xs text-textSecondary">Last reconciliation snapshot</p>
        </div>
        <div className="panel-body space-y-4">
          {accounts.length === 0 ? (
            <StateNotice
              title="No broker accounts synced yet."
              detail="Run broker sync to create local read-only snapshots."
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
                      Synced{" "}
                      {account.last_synced_at ? formatDateTime(account.last_synced_at) : "not yet"}
                    </p>
                  </div>
                </div>
                <div className="mt-3 overflow-auto">
                  <table className="min-w-full text-left">
                    <thead className="text-xs text-textSecondary">
                      <tr>
                        <th className="table-cell">Symbol</th>
                        <th className="table-cell">Qty</th>
                        <th className="table-cell">Avg Cost</th>
                        <th className="table-cell">Last</th>
                        <th className="table-cell">Market Value</th>
                      </tr>
                    </thead>
                    <tbody>
                      {account.positions.map((position) => (
                        <tr key={`${account.id}-${position.symbol}`} className="border-t border-border">
                          <td className="table-cell text-textPrimary">{position.symbol}</td>
                          <td className="table-cell text-textPrimary">{position.quantity.toFixed(4)}</td>
                          <td className="table-cell text-textSecondary">
                            {position.avg_cost !== null ? formatCurrency(position.avg_cost) : "N/A"}
                          </td>
                          <td className="table-cell text-textSecondary">
                            {position.market_price !== null ? formatCurrency(position.market_price) : "N/A"}
                          </td>
                          <td className="table-cell text-textPrimary">
                            {position.market_value !== null ? formatCurrency(position.market_value) : "N/A"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </article>
            ))
          )}
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-3">
        <div className="panel">
          <div className="panel-header">
            <h3 className="text-sm font-semibold text-textPrimary">Only Local</h3>
          </div>
          <div className="panel-body">
            {reconciliation.only_local.length === 0 ? (
              <StateNotice title="No local-only symbols." />
            ) : (
              <ul className="space-y-1 text-sm text-textPrimary">
                {reconciliation.only_local.map((symbol) => (
                  <li key={symbol}>{symbol}</li>
                ))}
              </ul>
            )}
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <h3 className="text-sm font-semibold text-textPrimary">Only Broker</h3>
          </div>
          <div className="panel-body">
            {reconciliation.only_broker.length === 0 ? (
              <StateNotice title="No broker-only symbols." />
            ) : (
              <ul className="space-y-1 text-sm text-textPrimary">
                {reconciliation.only_broker.map((symbol) => (
                  <li key={symbol}>{symbol}</li>
                ))}
              </ul>
            )}
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <h3 className="text-sm font-semibold text-textPrimary">Quantity Mismatches</h3>
          </div>
          <div className="panel-body">
            {reconciliation.quantity_mismatches.length === 0 ? (
              <StateNotice title="No quantity mismatches." />
            ) : (
              <ul className="space-y-2">
                {reconciliation.quantity_mismatches.map((row) => (
                  <li key={row.symbol} className="rounded-md border border-border px-3 py-2 text-xs">
                    <p className="text-sm text-textPrimary">{row.symbol}</p>
                    <p className="text-textSecondary">
                      Local {row.local_quantity.toFixed(4)} vs Broker {row.broker_quantity.toFixed(4)}
                    </p>
                    <p className={row.quantity_delta >= 0 ? "text-warning" : "text-danger"}>
                      Delta {row.quantity_delta >= 0 ? "+" : ""}
                      {row.quantity_delta.toFixed(4)}
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
