import type {
  AlertEvaluationSummary,
  AlertEvent,
  DailyBriefDetail,
  DashboardPayload,
  ManagedAlert,
  NoteSynthesis,
  NotificationItem,
  PortfolioOverviewPayload,
  ResearchNote,
  SecurityWorkspacePayload,
  Thesis,
  Watchlist,
  WatchlistLayoutState
} from "./types";

export const mockDashboard: DashboardPayload = {
  source_provider: "mock",
  as_of: new Date().toISOString(),
  delay_seconds: 900,
  freshness_status: "stale",
  is_stale: true,
  market_snapshot: [
    { symbol: "SPY", name: "SPDR S&P 500 ETF", price: 512.34, change: -3.12, change_percent: -0.61 },
    { symbol: "QQQ", name: "Invesco QQQ", price: 441.56, change: -4.95, change_percent: -1.11 },
    { symbol: "IWM", name: "iShares Russell 2000", price: 201.22, change: 1.43, change_percent: 0.72 }
  ],
  watchlists: [],
  movers: { gainers: [], losers: [] },
  macro_events: [],
  active_alerts: [],
  morning_brief: {
    id: "brief-fallback",
    headline: "Fallback brief",
    bullets: ["API unavailable. Showing cached fallback dataset."],
    generated_at: new Date().toISOString()
  }
};

export const mockWatchlists: Watchlist[] = [];

export const defaultLayoutState: WatchlistLayoutState = {
  sortBy: "symbol",
  sortDirection: "asc",
  filterTag: null
};

export const mockSecurityWorkspace = (symbol: string): SecurityWorkspacePayload => ({
  source_provider: "mock",
  as_of: new Date().toISOString(),
  delay_seconds: 900,
  freshness_status: "degraded",
  is_stale: true,
  instrument: {
    symbol,
    name: `${symbol} Placeholder Corp`,
    exchange: "NASDAQ",
    sector: "Technology",
    industry: "Software",
    market_cap: 100000000000,
    description: "Fallback security payload"
  },
  quote: {
    symbol,
    name: `${symbol} Placeholder Corp`,
    price: 100,
    change: 0,
    change_percent: 0
  },
  bars: [],
  indicators: {
    sma20: [],
    sma50: [],
    ema20: [],
    rsi14: [],
    macd: []
  },
  filings: [],
  notes: [],
  catalysts: [],
  what_changed: "No current provider response.",
  watchlists: []
});

export const mockResearchNotes: ResearchNote[] = [
  {
    id: "note-fallback-1",
    symbol: "AAPL",
    title: "Fallback thesis note",
    content: "Monitor services growth and margin quality.",
    note_type: "thesis",
    theme: "quality",
    sector: "Technology",
    event_ref: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  }
];

export const mockTheses: Thesis[] = [
  {
    id: "thesis-fallback-1",
    symbol: "AAPL",
    title: "Fallback thesis",
    status: "active",
    summary: "Services mix and capital return underpin medium-term thesis.",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  }
];

export const mockNoteSynthesis: NoteSynthesis = {
  scope_symbol: "AAPL",
  scope_theme: null,
  generated_at: new Date().toISOString(),
  source_model: "fallback",
  explanation: "Fallback synthesis because API was unavailable.",
  note_count: 1,
  thesis_count: 1,
  synthesized_thesis: "Services mix and capital return underpin medium-term thesis.",
  open_questions: ["What data point would invalidate this thesis in the next quarter?"],
  risks: ["Demand softening in key regions could pressure margin trajectory."],
  next_watch: ["Next earnings and guidance update."]
};

export const mockPortfolioOverview: PortfolioOverviewPayload = {
  portfolio: {
    id: "portfolio-fallback-1",
    name: "Personal",
    base_currency: "USD"
  },
  as_of: new Date().toISOString(),
  summary: {
    market_value: 14500,
    cost_basis: 13200,
    unrealized_pnl: 900,
    realized_pnl: 400,
    total_pnl: 1300,
    position_count: 2
  },
  holdings: [
    {
      instrument_id: "ins-aapl",
      symbol: "AAPL",
      name: "Apple Inc.",
      sector: "Technology",
      quantity: 20,
      avg_cost: 198.5,
      last_price: 219.15,
      market_value: 4383,
      cost_basis: 3970,
      unrealized_pnl: 413,
      realized_pnl: 180,
      note_count: 2,
      active_thesis_count: 1,
      watchlists: ["Core"]
    },
    {
      instrument_id: "ins-msft",
      symbol: "MSFT",
      name: "Microsoft Corporation",
      sector: "Technology",
      quantity: 12,
      avg_cost: 411.75,
      last_price: 423.62,
      market_value: 5083.44,
      cost_basis: 4941,
      unrealized_pnl: 142.44,
      realized_pnl: 220,
      note_count: 1,
      active_thesis_count: 1,
      watchlists: ["Core"]
    }
  ],
  exposures: [
    {
      sector: "Technology",
      market_value: 9466.44,
      weight: 1
    }
  ],
  transactions: [
    {
      id: "txn-fallback-1",
      symbol: "AAPL",
      trade_date: new Date().toISOString(),
      side: "buy",
      quantity: 20,
      price: 198.5,
      fees: 1,
      notional: 3970,
      notes: "Fallback transaction"
    }
  ]
};

export const mockManagedAlerts: ManagedAlert[] = [
  {
    id: "alert-fallback-1",
    symbol: "AAPL",
    alert_type: "price_threshold",
    rule: { operator: ">=", target: 220, cooldown_minutes: 60, interval_minutes: 5 },
    status: "active",
    next_eval_at: new Date().toISOString(),
    last_eval_at: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  }
];

export const mockAlertEvents: AlertEvent[] = [
  {
    id: "alert-event-fallback-1",
    alert_id: "alert-fallback-1",
    symbol: "AAPL",
    triggered_at: new Date().toISOString(),
    explanation: "AAPL price 221.50 >= threshold 220.00.",
    severity: "medium",
    payload: { symbol: "AAPL", price: 221.5, target: 220, operator: ">=" }
  }
];

export const mockNotifications: NotificationItem[] = [
  {
    id: "notification-fallback-1",
    title: "Alert triggered: AAPL",
    body: "AAPL price 221.50 >= threshold 220.00.",
    status: "sent",
    channel: "in_app",
    read_at: null,
    created_at: new Date().toISOString(),
    alert_event_id: "alert-event-fallback-1",
    daily_brief_id: null
  }
];

export const mockAlertEvaluationSummary: AlertEvaluationSummary = {
  evaluated_count: 1,
  triggered_count: 1,
  notifications_created: 1,
  evaluated_at: new Date().toISOString()
};

export const mockDailyBriefDetail: DailyBriefDetail = {
  id: "brief-fallback-1",
  headline: "Fallback brief generated from local data.",
  bullets: [
    "SPY: 512.34 (-0.61%)",
    "Watchlists: 2 lists / 7 tracked symbols.",
    "Template brief only; provider unavailable."
  ],
  body: "Fallback daily brief body.",
  generated_at: new Date().toISOString(),
  source_model: "fallback"
};
