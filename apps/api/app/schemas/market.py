from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import FreshnessEnvelope


class QuoteView(BaseModel):
    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    volume: float | None = None


class WatchlistItemView(BaseModel):
    id: str
    symbol: str
    instrument_name: str
    tags: list[str]
    sort_order: int
    quote: QuoteView


class WatchlistView(BaseModel):
    id: str
    name: str
    description: str | None
    items: list[WatchlistItemView]


class MoversView(BaseModel):
    gainers: list[QuoteView]
    losers: list[QuoteView]


class MacroEventView(BaseModel):
    id: str
    title: str
    scheduled_at: datetime
    impact: str
    actual: str | None
    forecast: str | None


class AlertDigestView(BaseModel):
    id: str
    symbol: str
    rule_summary: str
    status: str
    triggered_at: datetime | None


class MorningBriefView(BaseModel):
    id: str
    headline: str
    bullets: list[str]
    generated_at: datetime


class DashboardResponse(FreshnessEnvelope):
    market_snapshot: list[QuoteView]
    watchlists: list[WatchlistView]
    movers: MoversView
    macro_events: list[MacroEventView]
    active_alerts: list[AlertDigestView]
    morning_brief: MorningBriefView
