from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_cache, get_provider, get_user_id
from app.db.session import get_db
from app.schemas.market import DashboardResponse
from app.schemas.prices import HistoricalBarsResponse
from app.schemas.workspace import SecurityWorkspaceResponse
from app.services.cache import CacheService
from app.services.market import MarketWorkspaceService
from app.services.market_provider import MarketDataProvider

router = APIRouter(prefix="", tags=["market"])


@router.get("/market/dashboard", response_model=DashboardResponse)
def get_dashboard(
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_provider),
    cache: CacheService = Depends(get_cache),
    user_id: str = Depends(get_user_id),
) -> dict[str, object]:
    return MarketWorkspaceService(db, provider, cache).dashboard(user_id)


@router.get("/instruments/search")
def search_instruments(
    q: str = Query(default="", min_length=0),
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_provider),
    cache: CacheService = Depends(get_cache),
) -> dict[str, object]:
    service = MarketWorkspaceService(db, provider, cache)
    return {"results": service.instrument_search(q)}


@router.get("/instruments/{symbol}")
def get_instrument(
    symbol: str,
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_provider),
    cache: CacheService = Depends(get_cache),
) -> dict[str, object]:
    service = MarketWorkspaceService(db, provider, cache)
    payload = service.instrument_detail(symbol)
    if payload is None:
        raise HTTPException(status_code=404, detail="Instrument not found")
    return payload


@router.get("/quotes/snapshots")
def get_quote_snapshots(
    symbols: str = Query(..., description="Comma-separated symbols"),
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_provider),
    cache: CacheService = Depends(get_cache),
) -> dict[str, object]:
    normalized = [symbol.strip().upper() for symbol in symbols.split(",") if symbol.strip()]
    return MarketWorkspaceService(db, provider, cache).quote_snapshots(normalized)


@router.get("/prices/bars/{symbol}", response_model=HistoricalBarsResponse)
def get_bars(
    symbol: str,
    timeframe: str = Query(default="6M"),
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_provider),
    cache: CacheService = Depends(get_cache),
) -> dict[str, object]:
    return MarketWorkspaceService(db, provider, cache).bars(symbol, timeframe)


@router.get("/workspaces/security/{symbol}", response_model=SecurityWorkspaceResponse)
def get_security_workspace(
    symbol: str,
    timeframe: str = Query(default="6M"),
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_provider),
    cache: CacheService = Depends(get_cache),
    user_id: str = Depends(get_user_id),
) -> dict[str, object]:
    payload = MarketWorkspaceService(db, provider, cache).security_workspace(
        symbol=symbol,
        user_id=user_id,
        timeframe=timeframe,
    )
    if payload is None:
        raise HTTPException(status_code=404, detail="Security workspace not found")
    return payload
