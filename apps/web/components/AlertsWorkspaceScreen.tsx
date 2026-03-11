"use client";

import { useState } from "react";

import {
  createManagedAlert,
  deleteManagedAlert,
  evaluateAlerts,
  generateBrief,
  getAlertEvents,
  getManagedAlerts,
  getNotifications,
  markNotificationRead
} from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import type { AlertEvent, DailyBriefDetail, ManagedAlert, NotificationItem } from "@/lib/types";

interface AlertsWorkspaceScreenProps {
  initialAlerts: ManagedAlert[];
  initialEvents: AlertEvent[];
  initialNotifications: NotificationItem[];
  initialBrief: DailyBriefDetail;
}

interface AlertDraft {
  symbol: string;
  alertType: "price_threshold" | "percent_move";
  operator: ">" | ">=" | "<" | "<=";
  target: string;
  cooldownMinutes: string;
  intervalMinutes: string;
}

const defaultDraft: AlertDraft = {
  symbol: "",
  alertType: "price_threshold",
  operator: ">=",
  target: "",
  cooldownMinutes: "60",
  intervalMinutes: "5"
};

export function AlertsWorkspaceScreen({
  initialAlerts,
  initialEvents,
  initialNotifications,
  initialBrief
}: AlertsWorkspaceScreenProps) {
  const [alerts, setAlerts] = useState(initialAlerts);
  const [events, setEvents] = useState(initialEvents);
  const [notifications, setNotifications] = useState(initialNotifications);
  const [brief, setBrief] = useState(initialBrief);
  const [draft, setDraft] = useState(defaultDraft);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isBusy, setIsBusy] = useState(false);

  async function refreshWorkspace() {
    const [nextAlerts, nextEvents, nextNotifications] = await Promise.all([
      getManagedAlerts("all"),
      getAlertEvents(),
      getNotifications("all")
    ]);
    setAlerts(nextAlerts);
    setEvents(nextEvents);
    setNotifications(nextNotifications);
  }

  async function onCreateAlert() {
    const symbol = draft.symbol.trim().toUpperCase();
    const target = Number(draft.target);
    if (!symbol || !Number.isFinite(target)) {
      setError("Symbol and numeric target are required.");
      return;
    }

    setIsBusy(true);
    try {
      await createManagedAlert({
        symbol,
        alert_type: draft.alertType,
        rule: {
          operator: draft.operator,
          target,
          cooldown_minutes: Number(draft.cooldownMinutes) || 60,
          interval_minutes: Number(draft.intervalMinutes) || 5
        }
      });
      setDraft(defaultDraft);
      setMessage("Alert created.");
      setError(null);
      await refreshWorkspace();
    } catch {
      setError("Unable to create alert.");
    } finally {
      setIsBusy(false);
    }
  }

  async function onDeleteAlert(alertId: string) {
    setIsBusy(true);
    try {
      await deleteManagedAlert(alertId);
      setMessage("Alert deleted.");
      setError(null);
      await refreshWorkspace();
    } catch {
      setError("Unable to delete alert.");
    } finally {
      setIsBusy(false);
    }
  }

  async function onEvaluateAlerts() {
    setIsBusy(true);
    try {
      const summary = await evaluateAlerts();
      setMessage(
        `Evaluated ${summary.evaluated_count} alerts, triggered ${summary.triggered_count}, notifications ${summary.notifications_created}.`
      );
      setError(null);
      await refreshWorkspace();
    } catch {
      setError("Unable to evaluate alerts.");
    } finally {
      setIsBusy(false);
    }
  }

  async function onGenerateBrief() {
    setIsBusy(true);
    try {
      const generated = await generateBrief();
      setBrief(generated);
      setMessage("Daily brief generated.");
      setError(null);
      const refreshedNotifications = await getNotifications("all");
      setNotifications(refreshedNotifications);
    } catch {
      setError("Unable to generate daily brief.");
    } finally {
      setIsBusy(false);
    }
  }

  async function onMarkRead(notificationId: string) {
    setIsBusy(true);
    try {
      await markNotificationRead(notificationId);
      setError(null);
      const refreshed = await getNotifications("all");
      setNotifications(refreshed);
    } catch {
      setError("Unable to mark notification as read.");
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.16em] text-textSecondary">Phase 5</p>
          <h2 className="text-2xl font-semibold text-textPrimary">Alerts & Briefs</h2>
        </div>
        <button
          type="button"
          onClick={() => {
            void onEvaluateAlerts();
          }}
          className="ml-auto rounded-md border border-border px-3 py-2 text-xs text-textSecondary hover:text-textPrimary"
          disabled={isBusy}
        >
          Evaluate Alerts Now
        </button>
      </div>

      {message ? (
        <div className="rounded-md border border-success/40 bg-success/10 px-3 py-2 text-sm text-success">
          {message}
        </div>
      ) : null}
      {error ? (
        <div className="rounded-md border border-danger/40 bg-danger/10 px-3 py-2 text-sm text-danger">
          {error}
        </div>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[1.2fr,1fr]">
        <section className="panel">
          <div className="panel-header">
            <h3 className="text-sm font-semibold text-textPrimary">Create Alert</h3>
            <p className="text-xs text-textSecondary">Price threshold and percent-move rules</p>
          </div>
          <div className="panel-body grid gap-2 md:grid-cols-3">
            <input
              value={draft.symbol}
              onChange={(event) => setDraft((prev) => ({ ...prev, symbol: event.target.value }))}
              placeholder="Symbol"
              className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
            />
            <select
              value={draft.alertType}
              onChange={(event) =>
                setDraft((prev) => ({
                  ...prev,
                  alertType: event.target.value as AlertDraft["alertType"]
                }))
              }
              className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
            >
              <option value="price_threshold">price_threshold</option>
              <option value="percent_move">percent_move</option>
            </select>
            <select
              value={draft.operator}
              onChange={(event) =>
                setDraft((prev) => ({ ...prev, operator: event.target.value as AlertDraft["operator"] }))
              }
              className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
            >
              <option value=">=">{">="}</option>
              <option value=">">{">"}</option>
              <option value="<=">{"<="}</option>
              <option value="<">{"<"}</option>
            </select>
            <input
              value={draft.target}
              onChange={(event) => setDraft((prev) => ({ ...prev, target: event.target.value }))}
              placeholder="Target"
              type="number"
              className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
            />
            <input
              value={draft.cooldownMinutes}
              onChange={(event) =>
                setDraft((prev) => ({ ...prev, cooldownMinutes: event.target.value }))
              }
              placeholder="Cooldown (min)"
              type="number"
              className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
            />
            <input
              value={draft.intervalMinutes}
              onChange={(event) =>
                setDraft((prev) => ({ ...prev, intervalMinutes: event.target.value }))
              }
              placeholder="Eval interval (min)"
              type="number"
              className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
            />
            <button
              type="button"
              onClick={() => {
                void onCreateAlert();
              }}
              className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-[#06121e]"
              disabled={isBusy}
            >
              Add Alert
            </button>
          </div>
        </section>

        <section className="panel">
          <div className="panel-header flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-textPrimary">Daily Brief</h3>
              <p className="text-xs text-textSecondary">Template brief generation</p>
            </div>
            <button
              type="button"
              onClick={() => {
                void onGenerateBrief();
              }}
              className="rounded-md border border-border px-3 py-1 text-xs text-textSecondary hover:text-textPrimary"
              disabled={isBusy}
            >
              Generate
            </button>
          </div>
          <div className="panel-body">
            <p className="text-sm font-medium text-textPrimary">{brief.headline}</p>
            <ul className="mt-2 space-y-1 text-xs text-textSecondary">
              {brief.bullets.map((bullet, index) => (
                <li key={`${brief.id}-${index}`}>• {bullet}</li>
              ))}
            </ul>
            {brief.body ? <p className="mt-3 text-xs text-textSecondary">{brief.body}</p> : null}
            <p className="mt-2 text-xs text-textSecondary">
              Generated {formatDateTime(brief.generated_at)} · {brief.source_model}
            </p>
          </div>
        </section>
      </div>

      <section className="panel">
        <div className="panel-header">
          <h3 className="text-sm font-semibold text-textPrimary">Active Alerts</h3>
        </div>
        <div className="panel-body overflow-auto">
          <table className="min-w-full">
            <thead className="text-left text-xs text-textSecondary">
              <tr>
                <th className="table-cell">Symbol</th>
                <th className="table-cell">Type</th>
                <th className="table-cell">Rule</th>
                <th className="table-cell">Status</th>
                <th className="table-cell">Next Eval</th>
                <th className="table-cell">Actions</th>
              </tr>
            </thead>
            <tbody>
              {alerts.map((alert) => (
                <tr key={alert.id} className="border-t border-border">
                  <td className="table-cell text-textPrimary">{alert.symbol ?? "MARKET"}</td>
                  <td className="table-cell text-textSecondary">{alert.alert_type}</td>
                  <td className="table-cell text-xs text-textSecondary">
                    {JSON.stringify(alert.rule)}
                  </td>
                  <td className="table-cell text-textSecondary">{alert.status}</td>
                  <td className="table-cell text-textSecondary">
                    {alert.next_eval_at ? formatDateTime(alert.next_eval_at) : "N/A"}
                  </td>
                  <td className="table-cell">
                    <button
                      type="button"
                      className="rounded border border-danger/40 px-2 py-1 text-xs text-danger"
                      onClick={() => {
                        void onDeleteAlert(alert.id);
                      }}
                      disabled={isBusy}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
              {alerts.length === 0 ? (
                <tr>
                  <td className="table-cell text-textSecondary" colSpan={6}>
                    No alerts configured.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>

      <div className="grid gap-6 xl:grid-cols-2">
        <section className="panel">
          <div className="panel-header">
            <h3 className="text-sm font-semibold text-textPrimary">Alert Events</h3>
          </div>
          <div className="panel-body space-y-2">
            {events.map((event) => (
              <article key={event.id} className="rounded-md border border-border px-3 py-2">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm text-textPrimary">{event.symbol ?? "MARKET"}</p>
                  <p className="text-xs text-textSecondary">{event.severity}</p>
                </div>
                <p className="mt-1 text-xs text-textSecondary">
                  {event.explanation ?? "No explanation"}
                </p>
                <p className="mt-1 text-xs text-textSecondary">
                  Triggered {formatDateTime(event.triggered_at)}
                </p>
              </article>
            ))}
            {events.length === 0 ? <p className="text-sm text-textSecondary">No events yet.</p> : null}
          </div>
        </section>

        <section className="panel">
          <div className="panel-header">
            <h3 className="text-sm font-semibold text-textPrimary">Notifications</h3>
          </div>
          <div className="panel-body space-y-2">
            {notifications.map((item) => (
              <article key={item.id} className="rounded-md border border-border px-3 py-2">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm text-textPrimary">{item.title}</p>
                  <p className="text-xs text-textSecondary">
                    {item.read_at ? "read" : "unread"}
                  </p>
                </div>
                <p className="mt-1 text-xs text-textSecondary">{item.body}</p>
                <div className="mt-2 flex items-center justify-between">
                  <p className="text-xs text-textSecondary">{formatDateTime(item.created_at)}</p>
                  {!item.read_at ? (
                    <button
                      type="button"
                      className="rounded border border-border px-2 py-1 text-xs text-textSecondary hover:text-textPrimary"
                      onClick={() => {
                        void onMarkRead(item.id);
                      }}
                      disabled={isBusy}
                    >
                      Mark read
                    </button>
                  ) : null}
                </div>
              </article>
            ))}
            {notifications.length === 0 ? (
              <p className="text-sm text-textSecondary">No notifications.</p>
            ) : null}
          </div>
        </section>
      </div>
    </div>
  );
}
