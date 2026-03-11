from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_provider, get_user_id
from app.db.session import get_db
from app.schemas.watchlists import (
    AddWatchlistItemRequest,
    CreateWatchlistRequest,
    ReorderWatchlistItemsRequest,
    UpdateWatchlistRequest,
    WatchlistResponse,
)
from app.services.market_provider import MarketDataProvider
from app.services.watchlists import WatchlistService

router = APIRouter(prefix="/watchlists", tags=["watchlists"])


@router.get("", response_model=list[WatchlistResponse])
def list_watchlists(
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_provider),
    user_id: str = Depends(get_user_id),
) -> list[dict[str, object]]:
    return WatchlistService(db, provider).list_watchlists(user_id)


@router.post("", response_model=WatchlistResponse, status_code=status.HTTP_201_CREATED)
def create_watchlist(
    payload: CreateWatchlistRequest,
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_provider),
    user_id: str = Depends(get_user_id),
) -> dict[str, object]:
    return WatchlistService(db, provider).create_watchlist(user_id, payload.name, payload.description)


@router.patch("/{watchlist_id}", response_model=WatchlistResponse)
def patch_watchlist(
    watchlist_id: str,
    payload: UpdateWatchlistRequest,
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_provider),
    user_id: str = Depends(get_user_id),
) -> dict[str, object]:
    try:
        return WatchlistService(db, provider).update_watchlist(
            user_id,
            watchlist_id,
            payload.name,
            payload.description,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{watchlist_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_watchlist(
    watchlist_id: str,
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_provider),
    user_id: str = Depends(get_user_id),
) -> Response:
    try:
        WatchlistService(db, provider).delete_watchlist(user_id, watchlist_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{watchlist_id}/items", response_model=WatchlistResponse)
def add_watchlist_item(
    watchlist_id: str,
    payload: AddWatchlistItemRequest,
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_provider),
    user_id: str = Depends(get_user_id),
) -> dict[str, object]:
    try:
        return WatchlistService(db, provider).add_item(
            user_id,
            watchlist_id,
            payload.symbol,
            payload.tags,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/{watchlist_id}/items/reorder", response_model=WatchlistResponse)
def reorder_watchlist_items(
    watchlist_id: str,
    payload: ReorderWatchlistItemsRequest,
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_provider),
    user_id: str = Depends(get_user_id),
) -> dict[str, object]:
    try:
        return WatchlistService(db, provider).reorder_items(user_id, watchlist_id, payload.item_ids)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{watchlist_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_watchlist_item(
    watchlist_id: str,
    item_id: str,
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_provider),
    user_id: str = Depends(get_user_id),
) -> Response:
    try:
        WatchlistService(db, provider).remove_item(user_id, watchlist_id, item_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
