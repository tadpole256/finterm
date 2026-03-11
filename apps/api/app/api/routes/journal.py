from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_user_id
from app.db.session import get_db
from app.schemas.journal import CreateTradeJournalEntryRequest, TradeJournalEntryView
from app.services.journal import JournalService

router = APIRouter(prefix="/journal", tags=["journal"])


@router.get("/entries", response_model=list[TradeJournalEntryView])
def list_journal_entries(
    symbol: str | None = Query(default=None),
    entry_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=250),
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    return JournalService(db).list_entries(
        user_id=user_id,
        symbol=symbol,
        entry_type=entry_type,
        limit=limit,
    )


@router.post("/entries", response_model=TradeJournalEntryView, status_code=status.HTTP_201_CREATED)
def create_journal_entry(
    payload: CreateTradeJournalEntryRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        return JournalService(db).create_entry(user_id=user_id, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
