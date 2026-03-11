from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class TradeJournalEntryView(BaseModel):
    id: str
    symbol: str | None
    entry_type: str
    title: str
    body: str
    tags: list[str]
    portfolio_id: str | None
    transaction_id: str | None
    broker_order_event_id: str | None
    created_at: datetime
    updated_at: datetime


class CreateTradeJournalEntryRequest(BaseModel):
    symbol: str | None = Field(default=None, max_length=24)
    entry_type: str = Field(default="observation", min_length=1, max_length=32)
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)
    portfolio_id: str | None = None
    transaction_id: str | None = None
    broker_order_event_id: str | None = None
