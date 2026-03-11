from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_provider, get_user_id
from app.db.session import get_db
from app.schemas.screening import (
    CreateSavedScreenRequest,
    SavedScreenRunResponse,
    SavedScreenView,
    ScreenerRunResponse,
    UpdateSavedScreenRequest,
)
from app.services.market_provider import MarketDataProvider
from app.services.screening import ScreenerFilters, ScreenerService

router = APIRouter(prefix="/screening", tags=["screening"])


@router.get("/run", response_model=ScreenerRunResponse)
def run_screening(
    price_min: float | None = Query(default=None),
    price_max: float | None = Query(default=None),
    market_cap_min: float | None = Query(default=None),
    market_cap_max: float | None = Query(default=None),
    change_percent_min: float | None = Query(default=None),
    change_percent_max: float | None = Query(default=None),
    volume_min: float | None = Query(default=None),
    volume_max: float | None = Query(default=None),
    sector: str | None = Query(default=None),
    asset_type: str | None = Query(default=None),
    symbol_query: str | None = Query(default=None),
    watchlist_id: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    sort_by: str = Query(default="symbol"),
    sort_direction: str = Query(default="asc"),
    limit: int = Query(default=250, ge=1, le=1000),
    user_id: str = Depends(get_user_id),
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
        volume_min=volume_min,
        volume_max=volume_max,
        sector=sector,
        asset_type=asset_type,
        symbol_query=symbol_query,
        watchlist_id=watchlist_id,
        tag=tag,
        sort_by=sort_by,
        sort_direction=sort_direction,
        limit=limit,
    )
    results = ScreenerService(db, provider).run(filters, user_id=user_id)
    return {"results": results}


@router.get("/screens", response_model=list[SavedScreenView])
def list_saved_screens(
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_provider),
) -> list[dict[str, object]]:
    return ScreenerService(db, provider).list_saved_screens(user_id=user_id)


@router.post("/screens", response_model=SavedScreenView, status_code=status.HTTP_201_CREATED)
def create_saved_screen(
    payload: CreateSavedScreenRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_provider),
) -> dict[str, object]:
    return ScreenerService(db, provider).create_saved_screen(
        user_id=user_id,
        name=payload.name,
        criteria=payload.criteria,
    )


@router.patch("/screens/{screen_id}", response_model=SavedScreenView)
def update_saved_screen(
    screen_id: str,
    payload: UpdateSavedScreenRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_provider),
) -> dict[str, object]:
    try:
        return ScreenerService(db, provider).update_saved_screen(
            user_id=user_id,
            screen_id=screen_id,
            name=payload.name,
            criteria=payload.criteria,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/screens/{screen_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_screen(
    screen_id: str,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_provider),
) -> Response:
    try:
        ScreenerService(db, provider).delete_saved_screen(user_id=user_id, screen_id=screen_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/screens/{screen_id}/run", response_model=SavedScreenRunResponse)
def run_saved_screen(
    screen_id: str,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_provider),
) -> dict[str, object]:
    try:
        return ScreenerService(db, provider).run_saved_screen(user_id=user_id, screen_id=screen_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
