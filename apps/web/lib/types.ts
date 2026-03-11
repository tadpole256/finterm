export type FreshnessStatus = "fresh" | "stale" | "degraded";

export interface MarketQuote {
  symbol: string;
  name: string;
  price: number;
  change: number;
  change_percent: number;
  volume?: number;
}

export interface WatchlistItem {
  id: string;
  symbol: string;
  instrument_name: string;
  tags: string[];
  sort_order: number;
  quote: MarketQuote;
}

export interface Watchlist {
  id: string;
  name: string;
  description: string | null;
  items: WatchlistItem[];
}

export interface MacroEvent {
  id: string;
  title: string;
  scheduled_at: string;
  impact: "low" | "medium" | "high";
  actual: string | null;
  forecast: string | null;
}

export interface AlertDigestItem {
  id: string;
  symbol: string;
  rule_summary: string;
  status: string;
  triggered_at: string | null;
}

export interface MorningBrief {
  id: string;
  headline: string;
  bullets: string[];
  generated_at: string;
}

export interface DashboardPayload {
  source_provider: string;
  as_of: string;
  delay_seconds: number;
  freshness_status: FreshnessStatus;
  is_stale: boolean;
  market_snapshot: MarketQuote[];
  watchlists: Watchlist[];
  movers: {
    gainers: MarketQuote[];
    losers: MarketQuote[];
  };
  macro_events: MacroEvent[];
  active_alerts: AlertDigestItem[];
  morning_brief: MorningBrief;
}

export interface BarPoint {
  ts: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface IndicatorSeriesPoint {
  ts: string;
  value: number | null;
}

export interface MacdPoint {
  ts: string;
  macd: number | null;
  signal: number | null;
  histogram: number | null;
}

export interface SecurityWorkspacePayload {
  source_provider: string;
  as_of: string;
  delay_seconds: number;
  freshness_status: FreshnessStatus;
  is_stale: boolean;
  instrument: {
    symbol: string;
    name: string;
    exchange: string;
    sector: string | null;
    industry: string | null;
    market_cap: number | null;
    description: string | null;
  };
  quote: MarketQuote;
  bars: BarPoint[];
  indicators: {
    sma20: IndicatorSeriesPoint[];
    sma50: IndicatorSeriesPoint[];
    ema20: IndicatorSeriesPoint[];
    rsi14: IndicatorSeriesPoint[];
    macd: MacdPoint[];
  };
  filings: Array<{
    id: string;
    form_type: string;
    filed_at: string;
    summary: string | null;
  }>;
  notes: Array<{
    id: string;
    title: string;
    note_type: string;
    updated_at: string;
  }>;
  catalysts: Array<{
    id: string;
    title: string;
    event_date: string;
    status: string;
  }>;
  what_changed: string;
  watchlists: Array<{
    id: string;
    name: string;
    is_member: boolean;
  }>;
}

export interface WatchlistLayoutState {
  sortBy: "symbol" | "price" | "change";
  sortDirection: "asc" | "desc";
  filterTag: string | null;
}

export interface ResearchNote {
  id: string;
  symbol: string | null;
  title: string;
  content: string;
  note_type: string;
  theme: string | null;
  sector: string | null;
  event_ref: string | null;
  created_at: string;
  updated_at: string;
}

export interface Thesis {
  id: string;
  symbol: string | null;
  title: string;
  status: string;
  summary: string;
  created_at: string;
  updated_at: string;
}

export interface NoteSynthesis {
  scope_symbol: string | null;
  scope_theme: string | null;
  generated_at: string;
  source_model: string;
  explanation: string;
  note_count: number;
  thesis_count: number;
  synthesized_thesis: string;
  open_questions: string[];
  risks: string[];
  next_watch: string[];
}

export interface PortfolioHeader {
  id: string;
  name: string;
  base_currency: string;
}

export interface PortfolioSummary {
  market_value: number;
  cost_basis: number;
  unrealized_pnl: number;
  realized_pnl: number;
  total_pnl: number;
  position_count: number;
}

export interface PortfolioHolding {
  instrument_id: string;
  symbol: string;
  name: string;
  sector: string | null;
  quantity: number;
  avg_cost: number;
  last_price: number | null;
  market_value: number | null;
  cost_basis: number;
  unrealized_pnl: number | null;
  realized_pnl: number;
  note_count: number;
  active_thesis_count: number;
  watchlists: string[];
}

export interface PortfolioExposure {
  sector: string;
  market_value: number;
  weight: number;
}

export type PortfolioTransactionSide = "buy" | "sell";

export interface PortfolioTransaction {
  id: string;
  symbol: string;
  trade_date: string;
  side: PortfolioTransactionSide;
  quantity: number;
  price: number;
  fees: number;
  notional: number;
  notes: string | null;
}

export interface PortfolioOverviewPayload {
  portfolio: PortfolioHeader;
  as_of: string;
  summary: PortfolioSummary;
  holdings: PortfolioHolding[];
  exposures: PortfolioExposure[];
  transactions: PortfolioTransaction[];
}

export interface AlertRuleConfig {
  operator?: ">" | ">=" | "<" | "<=" | "==" | string;
  target?: number;
  cooldown_minutes?: number;
  interval_minutes?: number;
  absolute?: boolean;
  [key: string]: string | number | boolean | undefined;
}

export interface ManagedAlert {
  id: string;
  symbol: string | null;
  alert_type: string;
  rule: AlertRuleConfig;
  status: string;
  next_eval_at: string | null;
  last_eval_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface AlertEvent {
  id: string;
  alert_id: string;
  symbol: string | null;
  triggered_at: string;
  explanation: string | null;
  severity: string;
  payload: Record<string, unknown>;
}

export interface NotificationItem {
  id: string;
  title: string;
  body: string;
  status: string;
  channel: string;
  read_at: string | null;
  created_at: string;
  alert_event_id: string | null;
  daily_brief_id: string | null;
}

export interface AlertEvaluationSummary {
  evaluated_count: number;
  triggered_count: number;
  notifications_created: number;
  evaluated_at: string;
}

export interface DailyBriefDetail {
  id: string;
  headline: string;
  bullets: string[];
  body: string | null;
  generated_at: string;
  source_model: string;
}
