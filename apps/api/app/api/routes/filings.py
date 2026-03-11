from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_filings_provider
from app.db.session import get_db
from app.schemas.filings import FilingDetailView, FilingSyncResponse, FilingView
from app.services.filings import FilingsService
from app.services.filings_provider import FilingsProvider

router = APIRouter(prefix="/filings", tags=["filings"])


@router.post("/sync", response_model=FilingSyncResponse)
def sync_filings(
    since: datetime | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    provider: FilingsProvider = Depends(get_filings_provider),
) -> dict[str, object]:
    return FilingsService(db, provider).sync_recent_filings(since=since, limit=limit)


@router.get("", response_model=list[FilingView])
def list_filings(
    symbol: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    provider: FilingsProvider = Depends(get_filings_provider),
) -> list[dict[str, object]]:
    return FilingsService(db, provider).list_filings(symbol=symbol, limit=limit)


@router.get("/{filing_id}", response_model=FilingDetailView)
def filing_detail(
    filing_id: str,
    db: Session = Depends(get_db),
    provider: FilingsProvider = Depends(get_filings_provider),
) -> dict[str, object]:
    payload = FilingsService(db, provider).get_filing_detail(filing_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Filing not found")
    return payload
