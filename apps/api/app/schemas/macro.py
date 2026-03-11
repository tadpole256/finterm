from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class MacroSeriesView(BaseModel):
    id: str
    code: str
    name: str
    description: str | None
    frequency: str
    source_provider: str
    upcoming_event_count: int
    next_event_at: datetime | None


class MacroEventView(BaseModel):
    id: str
    series_code: str | None
    title: str
    scheduled_at: datetime
    impact: str
    actual: str | None
    forecast: str | None
    country: str


class MacroSyncResponse(BaseModel):
    series_upserted: int
    events_inserted: int
    as_of: datetime
