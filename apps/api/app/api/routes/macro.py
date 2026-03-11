from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_macro_provider
from app.db.session import get_db
from app.schemas.macro import MacroEventView, MacroSeriesView, MacroSyncResponse
from app.services.macro import MacroService
from app.services.macro_provider import MacroProvider

router = APIRouter(prefix="/macro", tags=["macro"])


@router.post("/sync", response_model=MacroSyncResponse)
def sync_macro(
    db: Session = Depends(get_db),
    provider: MacroProvider = Depends(get_macro_provider),
) -> dict[str, object]:
    return MacroService(db, provider).sync()


@router.get("/series", response_model=list[MacroSeriesView])
def list_macro_series(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    provider: MacroProvider = Depends(get_macro_provider),
) -> list[dict[str, object]]:
    return MacroService(db, provider).list_series(limit=limit)


@router.get("/events", response_model=list[MacroEventView])
def list_macro_events(
    days_ahead: int = Query(default=14, ge=1, le=90),
    country: str | None = Query(default=None),
    impact: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
    db: Session = Depends(get_db),
    provider: MacroProvider = Depends(get_macro_provider),
) -> list[dict[str, object]]:
    return MacroService(db, provider).list_events(
        days_ahead=days_ahead,
        country=country,
        impact=impact,
        limit=limit,
    )
