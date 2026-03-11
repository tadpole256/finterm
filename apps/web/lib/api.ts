import {
  mockAlertEvaluationSummary,
  mockAlertEvents,
  mockBrokerAccounts,
  mockBrokerCapabilityStatus,
  mockBrokerOrderEvents,
  mockBrokerOrderPreview,
  mockBrokerReconciliation,
  mockBrokerSyncSummary,
  mockDailyBriefDetail,
  defaultLayoutState,
  mockFilings,
  mockFilingSyncSummary,
  mockDashboard,
  mockManagedAlerts,
  mockMacroEvents,
  mockMacroSeries,
  mockMacroSyncSummary,
  mockNoteSynthesis,
  mockNotifications,
  mockPortfolioOverview,
  mockPortfolioRiskSnapshot,
  mockReconciliationExceptions,
  mockResearchQaResponse,
  mockResearchNotes,
  mockSavedScreens,
  mockScreenerResults,
  mockSecurityWorkspace,
  mockTradeJournalEntries,
  mockTheses,
  mockWatchlists
} from "./mock";
import type {
  AlertEvaluationSummary,
  AlertEvent,
  BrokerAccount,
  BrokerCapabilityStatus,
  BrokerOrderEvent,
  BrokerOrderPreview,
  BrokerReconciliation,
  BrokerSyncSummary,
  DashboardPayload,
  DailyBriefDetail,
  FilingRecord,
  FilingSyncSummary,
  ManagedAlert,
  MacroEventRecord,
  MacroSeriesRecord,
  MacroSyncSummary,
  SavedScreen,
  ScreenerFilters,
  ScreenerResult,
  NoteSynthesis,
  NotificationItem,
  PortfolioOverviewPayload,
  PortfolioRiskSnapshot,
  PortfolioTransaction,
  PortfolioTransactionSide,
  ReconciliationException,
  ResearchQaResponse,
  ResearchNote,
  SecurityWorkspacePayload,
  Thesis,
  TradeJournalEntry,
  Watchlist,
  WatchlistLayoutState
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    },
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const responseText = await response.text();
  if (!responseText) {
    return undefined as T;
  }

  return JSON.parse(responseText) as T;
}

export async function getDashboard(): Promise<DashboardPayload> {
  try {
    return await request<DashboardPayload>("/api/v1/market/dashboard");
  } catch {
    return mockDashboard;
  }
}

export async function getWatchlists(): Promise<Watchlist[]> {
  try {
    return await request<Watchlist[]>("/api/v1/watchlists");
  } catch {
    return mockWatchlists;
  }
}

export async function createWatchlist(name: string, description: string | null): Promise<Watchlist> {
  return request<Watchlist>("/api/v1/watchlists", {
    method: "POST",
    body: JSON.stringify({ name, description })
  });
}

export async function addWatchlistItem(
  watchlistId: string,
  symbol: string,
  tags: string[]
): Promise<Watchlist> {
  return request<Watchlist>(`/api/v1/watchlists/${watchlistId}/items`, {
    method: "POST",
    body: JSON.stringify({ symbol, tags })
  });
}

export async function removeWatchlistItem(watchlistId: string, itemId: string): Promise<void> {
  await request<void>(`/api/v1/watchlists/${watchlistId}/items/${itemId}`, {
    method: "DELETE"
  });
}

export async function reorderWatchlistItems(
  watchlistId: string,
  itemIds: string[]
): Promise<Watchlist> {
  return request<Watchlist>(`/api/v1/watchlists/${watchlistId}/items/reorder`, {
    method: "PATCH",
    body: JSON.stringify({ item_ids: itemIds })
  });
}

export async function updateWatchlistLayout(
  userId: string,
  layout: WatchlistLayoutState
): Promise<WatchlistLayoutState> {
  try {
    const response = await request<{ state: WatchlistLayoutState }>(
      `/api/v1/workspaces/layout/watchlists?user_id=${encodeURIComponent(userId)}`,
      {
        method: "PUT",
        body: JSON.stringify({ state: layout })
      }
    );
    return response.state;
  } catch {
    return layout;
  }
}

export async function getWatchlistLayout(userId: string): Promise<WatchlistLayoutState> {
  try {
    const response = await request<{ state: WatchlistLayoutState }>(
      `/api/v1/workspaces/layout/watchlists?user_id=${encodeURIComponent(userId)}`
    );
    return response.state;
  } catch {
    return defaultLayoutState;
  }
}

export async function getSecurityWorkspace(
  symbol: string,
  timeframe = "6M"
): Promise<SecurityWorkspacePayload> {
  try {
    return await request<SecurityWorkspacePayload>(
      `/api/v1/workspaces/security/${symbol}?timeframe=${encodeURIComponent(timeframe)}`
    );
  } catch {
    return mockSecurityWorkspace(symbol);
  }
}

export interface GetResearchNotesParams {
  q?: string;
  symbol?: string;
  note_type?: string;
  theme?: string;
  limit?: number;
}

export async function getResearchNotes(params: GetResearchNotesParams = {}): Promise<ResearchNote[]> {
  try {
    const query = new URLSearchParams();
    if (params.q) {
      query.set("q", params.q);
    }
    if (params.symbol) {
      query.set("symbol", params.symbol);
    }
    if (params.note_type) {
      query.set("note_type", params.note_type);
    }
    if (params.theme) {
      query.set("theme", params.theme);
    }
    if (params.limit) {
      query.set("limit", String(params.limit));
    }
    const suffix = query.size > 0 ? `?${query.toString()}` : "";
    return await request<ResearchNote[]>(`/api/v1/research/notes${suffix}`);
  } catch {
    return mockResearchNotes;
  }
}

export async function createResearchNote(
  payload: Omit<ResearchNote, "id" | "created_at" | "updated_at">
): Promise<ResearchNote> {
  return request<ResearchNote>("/api/v1/research/notes", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function updateResearchNote(
  noteId: string,
  payload: Partial<Omit<ResearchNote, "id" | "created_at" | "updated_at">>
): Promise<ResearchNote> {
  return request<ResearchNote>(`/api/v1/research/notes/${noteId}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export async function deleteResearchNote(noteId: string): Promise<void> {
  await request<void>(`/api/v1/research/notes/${noteId}`, {
    method: "DELETE"
  });
}

export async function getResearchTheses(symbol?: string): Promise<Thesis[]> {
  try {
    const suffix = symbol ? `?symbol=${encodeURIComponent(symbol)}` : "";
    return await request<Thesis[]>(`/api/v1/research/theses${suffix}`);
  } catch {
    return mockTheses;
  }
}

export async function createThesis(
  payload: Omit<Thesis, "id" | "created_at" | "updated_at">
): Promise<Thesis> {
  return request<Thesis>("/api/v1/research/theses", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function updateThesis(
  thesisId: string,
  payload: Partial<Omit<Thesis, "id" | "created_at" | "updated_at">>
): Promise<Thesis> {
  return request<Thesis>(`/api/v1/research/theses/${thesisId}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export async function deleteThesis(thesisId: string): Promise<void> {
  await request<void>(`/api/v1/research/theses/${thesisId}`, {
    method: "DELETE"
  });
}

export async function getResearchThemes(): Promise<string[]> {
  try {
    const response = await request<{ themes: string[] }>("/api/v1/research/themes");
    return response.themes;
  } catch {
    return ["quality"];
  }
}

export async function getNoteSynthesis(params: {
  symbol?: string;
  theme?: string;
}): Promise<NoteSynthesis> {
  try {
    const query = new URLSearchParams();
    if (params.symbol) {
      query.set("symbol", params.symbol);
    }
    if (params.theme) {
      query.set("theme", params.theme);
    }
    const suffix = query.size > 0 ? `?${query.toString()}` : "";
    return await request<NoteSynthesis>(`/api/v1/research/synthesis${suffix}`);
  } catch {
    return mockNoteSynthesis;
  }
}

export async function getResearchQa(params: {
  question: string;
  symbol?: string;
  limit?: number;
}): Promise<ResearchQaResponse> {
  try {
    const query = new URLSearchParams();
    query.set("question", params.question);
    if (params.symbol) {
      query.set("symbol", params.symbol);
    }
    if (params.limit) {
      query.set("limit", String(params.limit));
    }
    return await request<ResearchQaResponse>(`/api/v1/ai/research-qa?${query.toString()}`);
  } catch {
    return mockResearchQaResponse;
  }
}

export async function getPortfolioOverview(
  portfolioId?: string
): Promise<PortfolioOverviewPayload> {
  try {
    const suffix = portfolioId ? `?portfolio_id=${encodeURIComponent(portfolioId)}` : "";
    return await request<PortfolioOverviewPayload>(`/api/v1/portfolio/overview${suffix}`);
  } catch {
    return mockPortfolioOverview;
  }
}

export async function getPortfolioRisk(
  portfolioId?: string
): Promise<PortfolioRiskSnapshot> {
  try {
    const suffix = portfolioId ? `?portfolio_id=${encodeURIComponent(portfolioId)}` : "";
    return await request<PortfolioRiskSnapshot>(`/api/v1/portfolio/risk${suffix}`);
  } catch {
    return mockPortfolioRiskSnapshot;
  }
}

export interface CreatePortfolioTransactionPayload {
  portfolio_id?: string;
  symbol: string;
  trade_date?: string;
  side: PortfolioTransactionSide;
  quantity: number;
  price: number;
  fees?: number;
  notes?: string | null;
}

export async function createPortfolioTransaction(
  payload: CreatePortfolioTransactionPayload
): Promise<PortfolioTransaction> {
  return request<PortfolioTransaction>("/api/v1/portfolio/transactions", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function deletePortfolioTransaction(transactionId: string): Promise<void> {
  await request<void>(`/api/v1/portfolio/transactions/${transactionId}`, {
    method: "DELETE"
  });
}

export interface CreateManagedAlertPayload {
  symbol?: string | null;
  alert_type: string;
  rule: Record<string, unknown>;
  status?: string;
}

export interface UpdateManagedAlertPayload {
  symbol?: string | null;
  alert_type?: string;
  rule?: Record<string, unknown>;
  status?: string;
}

export async function getManagedAlerts(status = "all"): Promise<ManagedAlert[]> {
  try {
    return await request<ManagedAlert[]>(`/api/v1/alerts?status=${encodeURIComponent(status)}`);
  } catch {
    return mockManagedAlerts;
  }
}

export async function createManagedAlert(
  payload: CreateManagedAlertPayload
): Promise<ManagedAlert> {
  return request<ManagedAlert>("/api/v1/alerts", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function updateManagedAlert(
  alertId: string,
  payload: UpdateManagedAlertPayload
): Promise<ManagedAlert> {
  return request<ManagedAlert>(`/api/v1/alerts/${alertId}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export async function deleteManagedAlert(alertId: string): Promise<void> {
  await request<void>(`/api/v1/alerts/${alertId}`, {
    method: "DELETE"
  });
}

export async function evaluateAlerts(): Promise<AlertEvaluationSummary> {
  try {
    return await request<AlertEvaluationSummary>("/api/v1/alerts/evaluate", {
      method: "POST"
    });
  } catch {
    return mockAlertEvaluationSummary;
  }
}

export async function getAlertEvents(): Promise<AlertEvent[]> {
  try {
    return await request<AlertEvent[]>("/api/v1/alerts/events");
  } catch {
    return mockAlertEvents;
  }
}

export async function getNotifications(status = "all"): Promise<NotificationItem[]> {
  try {
    return await request<NotificationItem[]>(
      `/api/v1/notifications?status=${encodeURIComponent(status)}`
    );
  } catch {
    return mockNotifications;
  }
}

export async function markNotificationRead(notificationId: string): Promise<void> {
  await request<void>(`/api/v1/notifications/${notificationId}/read`, {
    method: "PATCH"
  });
}

export async function getLatestBrief(): Promise<DailyBriefDetail> {
  try {
    return await request<DailyBriefDetail>("/api/v1/briefs/latest");
  } catch {
    return mockDailyBriefDetail;
  }
}

export async function generateBrief(): Promise<DailyBriefDetail> {
  try {
    return await request<DailyBriefDetail>("/api/v1/briefs/generate", {
      method: "POST"
    });
  } catch {
    return mockDailyBriefDetail;
  }
}

export async function syncFilings(): Promise<FilingSyncSummary> {
  try {
    return await request<FilingSyncSummary>("/api/v1/filings/sync", {
      method: "POST"
    });
  } catch {
    return mockFilingSyncSummary;
  }
}

export async function getFilings(symbol?: string): Promise<FilingRecord[]> {
  try {
    const suffix = symbol ? `?symbol=${encodeURIComponent(symbol)}` : "";
    return await request<FilingRecord[]>(`/api/v1/filings${suffix}`);
  } catch {
    return mockFilings;
  }
}

export async function syncMacro(): Promise<MacroSyncSummary> {
  try {
    return await request<MacroSyncSummary>("/api/v1/macro/sync", {
      method: "POST"
    });
  } catch {
    return mockMacroSyncSummary;
  }
}

export async function getMacroSeries(): Promise<MacroSeriesRecord[]> {
  try {
    return await request<MacroSeriesRecord[]>("/api/v1/macro/series");
  } catch {
    return mockMacroSeries;
  }
}

export async function getMacroEvents(daysAhead = 14): Promise<MacroEventRecord[]> {
  try {
    return await request<MacroEventRecord[]>(`/api/v1/macro/events?days_ahead=${daysAhead}`);
  } catch {
    return mockMacroEvents;
  }
}

export async function runScreener(filters: ScreenerFilters = {}): Promise<ScreenerResult[]> {
  try {
    const query = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        query.set(key, String(value));
      }
    });
    const suffix = query.size > 0 ? `?${query.toString()}` : "";
    const response = await request<{ results: ScreenerResult[] }>(`/api/v1/screening/run${suffix}`);
    return response.results;
  } catch {
    return mockScreenerResults;
  }
}

export async function getSavedScreens(): Promise<SavedScreen[]> {
  try {
    return await request<SavedScreen[]>("/api/v1/screening/screens");
  } catch {
    return mockSavedScreens;
  }
}

export async function createSavedScreen(payload: {
  name: string;
  criteria: ScreenerFilters;
}): Promise<SavedScreen> {
  return request<SavedScreen>("/api/v1/screening/screens", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function updateSavedScreen(
  screenId: string,
  payload: {
    name?: string;
    criteria?: ScreenerFilters;
  }
): Promise<SavedScreen> {
  return request<SavedScreen>(`/api/v1/screening/screens/${screenId}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export async function deleteSavedScreen(screenId: string): Promise<void> {
  await request<void>(`/api/v1/screening/screens/${screenId}`, {
    method: "DELETE"
  });
}

export async function runSavedScreen(screenId: string): Promise<ScreenerResult[]> {
  try {
    const response = await request<{ results: ScreenerResult[] }>(
      `/api/v1/screening/screens/${screenId}/run`,
      {
        method: "POST"
      }
    );
    return response.results;
  } catch {
    return mockScreenerResults;
  }
}

export async function getBrokerAccounts(): Promise<BrokerAccount[]> {
  try {
    return await request<BrokerAccount[]>("/api/v1/broker/accounts");
  } catch {
    return mockBrokerAccounts;
  }
}

export async function getBrokerCapabilities(): Promise<BrokerCapabilityStatus> {
  try {
    return await request<BrokerCapabilityStatus>("/api/v1/broker/capabilities");
  } catch {
    return mockBrokerCapabilityStatus;
  }
}

export async function syncBroker(): Promise<BrokerSyncSummary> {
  try {
    return await request<BrokerSyncSummary>("/api/v1/broker/sync", {
      method: "POST"
    });
  } catch {
    return mockBrokerSyncSummary;
  }
}

export async function getBrokerReconciliation(portfolioId?: string): Promise<BrokerReconciliation> {
  try {
    const suffix = portfolioId ? `?portfolio_id=${encodeURIComponent(portfolioId)}` : "";
    return await request<BrokerReconciliation>(`/api/v1/broker/reconcile${suffix}`);
  } catch {
    return mockBrokerReconciliation;
  }
}

export interface PreviewBrokerOrderPayload {
  symbol: string;
  side: "buy" | "sell";
  order_type: "market" | "limit";
  quantity: number;
  limit_price?: number;
}

export async function previewBrokerOrder(
  payload: PreviewBrokerOrderPayload
): Promise<BrokerOrderPreview> {
  try {
    return await request<BrokerOrderPreview>("/api/v1/broker/orders/preview", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  } catch {
    return mockBrokerOrderPreview;
  }
}

export interface CreateBrokerOrderEventPayload {
  broker_account_id?: string | null;
  external_order_id: string;
  symbol: string;
  side: "buy" | "sell";
  order_type?: "market" | "limit";
  status?: string;
  quantity: number;
  limit_price?: number | null;
  filled_quantity?: number;
  avg_fill_price?: number | null;
  status_updated_at?: string | null;
  event_payload?: Record<string, unknown>;
  create_journal_entry?: boolean;
}

export async function createBrokerOrderEvent(
  payload: CreateBrokerOrderEventPayload
): Promise<BrokerOrderEvent> {
  return request<BrokerOrderEvent>("/api/v1/broker/order-events", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function getBrokerOrderEvents(params: {
  symbol?: string;
  status?: string;
  limit?: number;
} = {}): Promise<BrokerOrderEvent[]> {
  try {
    const query = new URLSearchParams();
    if (params.symbol) {
      query.set("symbol", params.symbol);
    }
    if (params.status) {
      query.set("status", params.status);
    }
    if (params.limit) {
      query.set("limit", String(params.limit));
    }
    const suffix = query.size > 0 ? `?${query.toString()}` : "";
    return await request<BrokerOrderEvent[]>(`/api/v1/broker/order-events${suffix}`);
  } catch {
    return mockBrokerOrderEvents;
  }
}

export async function getReconciliationExceptions(status = "open"): Promise<ReconciliationException[]> {
  try {
    return await request<ReconciliationException[]>(
      `/api/v1/broker/reconciliation-exceptions?status=${encodeURIComponent(status)}`
    );
  } catch {
    return mockReconciliationExceptions;
  }
}

export async function resolveReconciliationException(
  exceptionId: string,
  resolutionNote?: string
): Promise<ReconciliationException> {
  return request<ReconciliationException>(
    `/api/v1/broker/reconciliation-exceptions/${exceptionId}/resolve`,
    {
      method: "PATCH",
      body: JSON.stringify({ resolution_note: resolutionNote ?? null })
    }
  );
}

export async function getJournalEntries(params: {
  symbol?: string;
  entry_type?: string;
  limit?: number;
} = {}): Promise<TradeJournalEntry[]> {
  try {
    const query = new URLSearchParams();
    if (params.symbol) {
      query.set("symbol", params.symbol);
    }
    if (params.entry_type) {
      query.set("entry_type", params.entry_type);
    }
    if (params.limit) {
      query.set("limit", String(params.limit));
    }
    const suffix = query.size > 0 ? `?${query.toString()}` : "";
    return await request<TradeJournalEntry[]>(`/api/v1/journal/entries${suffix}`);
  } catch {
    return mockTradeJournalEntries;
  }
}

export interface CreateJournalEntryPayload {
  symbol?: string | null;
  entry_type?: string;
  title: string;
  body: string;
  tags?: string[];
  portfolio_id?: string | null;
  transaction_id?: string | null;
  broker_order_event_id?: string | null;
}

export async function createJournalEntry(
  payload: CreateJournalEntryPayload
): Promise<TradeJournalEntry> {
  return request<TradeJournalEntry>("/api/v1/journal/entries", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}
