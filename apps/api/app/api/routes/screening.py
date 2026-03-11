from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_provider
from app.db.session import get_db
from app.services.market_provider import MarketDataProvider
from app.services.screening import ScreenerFilters, ScreenerService

router = APIRouter(prefix="/screening", tags=["screening"])


@router.get("/run")
def run_screening(
    price_min: float | None = Query(default=None),
    price_max: float | None = Query(default=None),
    market_cap_min: float | None = Query(default=None),
    market_cap_max: float | None = Query(default=None),
    change_percent_min: float | None = Query(default=None),
    change_percent_max: float | None = Query(default=None),
    sector: str | None = Query(default=None),
    watchlist_id: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_provider),
) -> dict[str, object]:
    filters = ScreenerFilters(
        price_min=price_min,
        price_max=price_max,
        market_cap_min=market_cap_min,
        market_cap_max=market_cap_max,
        change_percent_min=change_percent_min,
        change_percent_max=change_percent_max,
        sector=sector,
        watchlist_id=watchlist_id,
        tag=tag,
    )
    results = ScreenerService(db, provider).run(filters)
    return {"results": results}
