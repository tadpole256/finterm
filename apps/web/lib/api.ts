import {
  mockAlertEvaluationSummary,
  mockAlertEvents,
  mockDailyBriefDetail,
  defaultLayoutState,
  mockDashboard,
  mockManagedAlerts,
  mockNoteSynthesis,
  mockNotifications,
  mockPortfolioOverview,
  mockResearchNotes,
  mockSecurityWorkspace,
  mockTheses,
  mockWatchlists
} from "./mock";
import type {
  AlertEvaluationSummary,
  AlertEvent,
  DashboardPayload,
  DailyBriefDetail,
  ManagedAlert,
  NoteSynthesis,
  NotificationItem,
  PortfolioOverviewPayload,
  PortfolioTransaction,
  PortfolioTransactionSide,
  ResearchNote,
  SecurityWorkspacePayload,
  Thesis,
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
