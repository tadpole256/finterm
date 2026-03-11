from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class FilingSummaryView(BaseModel):
    summary: str
    key_changes: list[str]
    risks: list[str]
    forward_looking: list[str]
    takeaway: str
    model_name: str


class FilingView(BaseModel):
    id: str
    symbol: str
    accession_no: str
    form_type: str
    filed_at: datetime
    period_end: datetime | None
    filing_url: str | None
    source_provider: str
    summary: FilingSummaryView | None


class FilingDetailView(FilingView):
    raw_text: str | None


class FilingSyncResponse(BaseModel):
    fetched_count: int
    inserted_count: int
    updated_summary_count: int
    as_of: datetime
