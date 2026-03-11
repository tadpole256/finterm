import type {
  AlertEvaluationSummary,
  AlertEvent,
  BrokerAccount,
  BrokerCapabilityStatus,
  BrokerOrderEvent,
  BrokerOrderPreview,
  BrokerReconciliation,
  BrokerSyncSummary,
  DailyBriefDetail,
  DashboardPayload,
  FilingRecord,
  FilingSyncSummary,
  MacroEventRecord,
  MacroSeriesRecord,
  MacroSyncSummary,
  SavedScreen,
  ScreenerResult,
  ManagedAlert,
  NoteSynthesis,
  NotificationItem,
  PortfolioOverviewPayload,
  PortfolioRiskSnapshot,
  ReconciliationException,
  ResearchQaResponse,
  ResearchNote,
  SecurityWorkspacePayload,
  TradeJournalEntry,
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

export const mockFilings: FilingRecord[] = [
  {
    id: "filing-fallback-1",
    symbol: "AAPL",
    accession_no: "0000320193-26-000011",
    form_type: "10-Q",
    filed_at: new Date().toISOString(),
    period_end: null,
    filing_url: "https://www.sec.gov/",
    source_provider: "mock_sec",
    summary: {
      summary: "Fallback filing summary for local UI rendering.",
      key_changes: ["Services commentary expanded versus prior filing."],
      risks: ["FX sensitivity remains noted."],
      forward_looking: ["Management expects stable margin progression."],
      takeaway: "Treat this as a seeded placeholder.",
      model_name: "fallback"
    }
  }
];

export const mockMacroSeries: MacroSeriesRecord[] = [
  {
    id: "macro-series-fallback-1",
    code: "US_CPI_YOY",
    name: "US CPI YoY",
    description: "Fallback macro series payload.",
    frequency: "monthly",
    source_provider: "mock_macro",
    upcoming_event_count: 1,
    next_event_at: new Date().toISOString()
  }
];

export const mockMacroEvents: MacroEventRecord[] = [
  {
    id: "macro-event-fallback-1",
    series_code: "US_CPI_YOY",
    title: "CPI (YoY)",
    scheduled_at: new Date().toISOString(),
    impact: "high",
    actual: null,
    forecast: "3.0%",
    country: "US"
  }
];

export const mockFilingSyncSummary: FilingSyncSummary = {
  fetched_count: 1,
  inserted_count: 1,
  updated_summary_count: 1,
  as_of: new Date().toISOString()
};

export const mockMacroSyncSummary: MacroSyncSummary = {
  series_upserted: 1,
  events_inserted: 1,
  as_of: new Date().toISOString()
};

export const mockScreenerResults: ScreenerResult[] = [
  {
    symbol: "AAPL",
    name: "Apple Inc.",
    sector: "Technology",
    asset_type: "equity",
    market_cap: 2965000000000,
    price: 219.15,
    change_percent: 0.57,
    volume: 63854000
  },
  {
    symbol: "MSFT",
    name: "Microsoft Corporation",
    sector: "Technology",
    asset_type: "equity",
    market_cap: 3128000000000,
    price: 423.62,
    change_percent: -0.66,
    volume: 24551000
  }
];

export const mockSavedScreens: SavedScreen[] = [
  {
    id: "screen-fallback-1",
    name: "Large Cap Tech",
    criteria: {
      sector: "Technology",
      price_min: 100,
      sort_by: "market_cap",
      sort_direction: "desc",
      limit: 50
    },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  }
];

export const mockBrokerAccounts: BrokerAccount[] = [
  {
    id: "broker-account-fallback-1",
    provider: "mock_broker",
    external_account_id: "paper-main",
    account_name: "Paper Main",
    account_type: "taxable",
    base_currency: "USD",
    status: "active",
    last_synced_at: new Date().toISOString(),
    account_meta: { connection: "simulated" },
    position_count: 3,
    total_market_value: 19233.7,
    positions: [
      {
        symbol: "AAPL",
        quantity: 42,
        avg_cost: 197.25,
        market_price: 219.15,
        market_value: 9204.3,
        as_of: new Date().toISOString()
      },
      {
        symbol: "MSFT",
        quantity: 14,
        avg_cost: 409.1,
        market_price: 423.62,
        market_value: 5930.68,
        as_of: new Date().toISOString()
      },
      {
        symbol: "SPY",
        quantity: 8,
        avg_cost: 506.0,
        market_price: 512.34,
        market_value: 4098.72,
        as_of: new Date().toISOString()
      }
    ]
  }
];

export const mockBrokerSyncSummary: BrokerSyncSummary = {
  run_id: "broker-sync-fallback-1",
  provider: "mock_broker",
  status: "completed",
  fetched_accounts: 1,
  fetched_positions: 3,
  started_at: new Date().toISOString(),
  completed_at: new Date().toISOString(),
  message: "Broker sync completed (fallback)."
};

export const mockBrokerReconciliation: BrokerReconciliation = {
  as_of: new Date().toISOString(),
  summary: {
    local_symbol_count: 2,
    broker_symbol_count: 3,
    only_local_count: 0,
    only_broker_count: 1,
    quantity_mismatch_count: 2
  },
  only_local: [],
  only_broker: ["SPY"],
  open_exception_count: 2,
  quantity_mismatches: [
    {
      symbol: "AAPL",
      local_quantity: 20,
      broker_quantity: 42,
      quantity_delta: 22,
      local_market_value: 4383,
      broker_market_value: 9204.3
    },
    {
      symbol: "MSFT",
      local_quantity: 12,
      broker_quantity: 14,
      quantity_delta: 2,
      local_market_value: 5083.44,
      broker_market_value: 5930.68
    }
  ]
};

export const mockBrokerCapabilityStatus: BrokerCapabilityStatus = {
  capabilities: {
    provider: "mock_broker",
    supports_positions: true,
    supports_order_preview: true,
    supports_order_submission: true,
    supports_reconciliation: true,
    requires_auth: false,
    trading_enabled: false,
    can_submit_orders: false,
    restrictions: ["BROKER_TRADING_ENABLED is false."]
  },
  session: {
    provider: "mock_broker",
    connected: true,
    auth_state: "simulated",
    last_refreshed_at: new Date().toISOString(),
    expires_at: new Date(Date.now() + 4 * 60 * 60 * 1000).toISOString()
  }
};

export const mockBrokerOrderPreview: BrokerOrderPreview = {
  provider: "mock_broker",
  symbol: "AAPL",
  side: "buy",
  order_type: "market",
  quantity: 10,
  reference_price: 219.15,
  estimated_notional: 2191.5,
  estimated_fees: 1.1,
  estimated_total_cash: 2192.6,
  can_submit: false,
  restrictions: ["Order submission disabled by configuration."],
  warnings: []
};

export const mockReconciliationExceptions: ReconciliationException[] = [
  {
    id: "recon-ex-1",
    symbol: "AAPL",
    issue_type: "quantity_mismatch",
    severity: "high",
    status: "open",
    local_quantity: 20,
    broker_quantity: 42,
    local_market_value: 4383,
    broker_market_value: 9204.3,
    detected_at: new Date().toISOString(),
    last_seen_at: new Date().toISOString(),
    resolved_at: null,
    resolution_note: null,
    details: { quantity_delta: 22 }
  },
  {
    id: "recon-ex-2",
    symbol: "SPY",
    issue_type: "only_broker",
    severity: "medium",
    status: "open",
    local_quantity: null,
    broker_quantity: null,
    local_market_value: null,
    broker_market_value: null,
    detected_at: new Date().toISOString(),
    last_seen_at: new Date().toISOString(),
    resolved_at: null,
    resolution_note: null,
    details: {}
  }
];

export const mockBrokerOrderEvents: BrokerOrderEvent[] = [
  {
    id: "broker-event-1",
    broker_account_id: "broker-account-fallback-1",
    external_order_id: "mock-order-001",
    symbol: "AAPL",
    side: "buy",
    order_type: "limit",
    status: "filled",
    quantity: 5,
    limit_price: 215.5,
    filled_quantity: 5,
    avg_fill_price: 215.4,
    submitted_at: new Date().toISOString(),
    status_updated_at: new Date().toISOString(),
    event_payload: { venue: "SIM" }
  }
];

export const mockTradeJournalEntries: TradeJournalEntry[] = [
  {
    id: "journal-1",
    symbol: "AAPL",
    entry_type: "broker_fill",
    title: "AAPL BUY filled",
    body: "External order mock-order-001 status=filled qty=5.0000 filled=5.0000.",
    tags: ["broker", "fill"],
    portfolio_id: "portfolio-fallback-1",
    transaction_id: null,
    broker_order_event_id: "broker-event-1",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  }
];

export const mockPortfolioRiskSnapshot: PortfolioRiskSnapshot = {
  portfolio: {
    id: "portfolio-fallback-1",
    name: "Personal",
    base_currency: "USD"
  },
  as_of: new Date().toISOString(),
  net_exposure: 1,
  gross_exposure: 1,
  concentration_hhi: 0.52,
  top_positions: [
    { symbol: "MSFT", market_value: 5083.44, weight: 0.54 },
    { symbol: "AAPL", market_value: 4383, weight: 0.46 }
  ],
  factor_exposures: [
    { factor: "growth", exposure: 0.93, method: "heuristic_sector_bucket_v1" },
    { factor: "quality", exposure: 0.45, method: "heuristic_sector_bucket_v1" },
    { factor: "duration_risk", exposure: 0.75, method: "heuristic_sector_bucket_v1" }
  ],
  scenarios: [
    {
      name: "Risk-Off Growth Shock",
      estimated_pnl: -1135.97,
      estimated_return: -0.12,
      assumptions: "Technology -12%, Consumer Discretionary -10%, all others -6%."
    },
    {
      name: "Rates +100bp",
      estimated_pnl: -757.31,
      estimated_return: -0.08,
      assumptions: "Technology -8%, Real Estate -10%, Financials +4%, all others -3%."
    },
    {
      name: "Soft Landing Risk-On",
      estimated_pnl: 662.65,
      estimated_return: 0.07,
      assumptions: "Technology +7%, Financials +5%, Healthcare +3%, all others +4%."
    }
  ]
};

export const mockResearchQaResponse: ResearchQaResponse = {
  question: "What are the key risks in AAPL?",
  symbol: "AAPL",
  answered_at: new Date().toISOString(),
  source_model: "hybrid-mock-hash-embed-v1",
  answer:
    "Question: What are the key risks in AAPL?\nHighest-signal context from your notes and filings:\n- Risk update: Valuation rich into CPI week.\n- AAPL 10-Q (2026-03-01): FX headwinds remain material.\nUse citations below to verify source details.",
  coverage_count: 2,
  total_candidates: 5,
  citations: [
    {
      source_type: "research_note",
      source_id: "note-fallback-1",
      symbol: "AAPL",
      title: "Risk update",
      snippet: "Valuation rich into CPI week.",
      score: 1.23,
      lexical_score: 0.8,
      semantic_score: 0.9,
      recency_score: 1.0,
      as_of: new Date().toISOString(),
      url: null
    },
    {
      source_type: "filing",
      source_id: "filing-fallback-1",
      symbol: "AAPL",
      title: "AAPL 10-Q (2026-03-01)",
      snippet: "FX headwinds remain material.",
      score: 1.05,
      lexical_score: 0.6,
      semantic_score: 0.75,
      recency_score: 0.9,
      as_of: new Date().toISOString(),
      url: "https://www.sec.gov/"
    }
  ]
};
