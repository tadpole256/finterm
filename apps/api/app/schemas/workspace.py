from pydantic import BaseModel

from app.schemas.common import FreshnessEnvelope
from app.schemas.market import QuoteView
from app.schemas.prices import BarPoint, IndicatorsResponse


class InstrumentDetailView(BaseModel):
    symbol: str
    name: str
    exchange: str
    sector: str | None
    industry: str | None
    market_cap: float | None
    description: str | None


class FilingView(BaseModel):
    id: str
    form_type: str
    filed_at: str
    summary: str | None


class NoteView(BaseModel):
    id: str
    title: str
    note_type: str
    updated_at: str


class CatalystView(BaseModel):
    id: str
    title: str
    event_date: str
    status: str


class WatchlistMembershipView(BaseModel):
    id: str
    name: str
    is_member: bool


class SecurityWorkspaceResponse(FreshnessEnvelope):
    instrument: InstrumentDetailView
    quote: QuoteView
    bars: list[BarPoint]
    indicators: IndicatorsResponse
    filings: list[FilingView]
    notes: list[NoteView]
    catalysts: list[CatalystView]
    what_changed: str
    watchlists: list[WatchlistMembershipView]
