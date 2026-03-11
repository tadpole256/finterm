from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_provider, get_user_id
from app.db.session import get_db
from app.schemas.portfolio import (
    CreateTransactionRequest,
    PortfolioOverviewResponse,
    PortfolioTransactionView,
    PositionsResponse,
    TransactionsResponse,
)
from app.services.market_provider import MarketDataProvider
from app.services.portfolio import PortfolioService

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/overview", response_model=PortfolioOverviewResponse)
def get_overview(
    portfolio_id: str | None = Query(default=None),
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_provider),
) -> dict[str, object]:
    try:
        return PortfolioService(db, provider).overview(user_id=user_id, portfolio_id=portfolio_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/positions", response_model=PositionsResponse)
def get_positions(
    portfolio_id: str | None = Query(default=None),
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_provider),
) -> dict[str, object]:
    try:
        return PortfolioService(db, provider).positions(user_id=user_id, portfolio_id=portfolio_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/transactions", response_model=TransactionsResponse)
def get_transactions(
    portfolio_id: str | None = Query(default=None),
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_provider),
) -> dict[str, object]:
    try:
        return PortfolioService(db, provider).transactions(user_id=user_id, portfolio_id=portfolio_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/transactions", response_model=PortfolioTransactionView, status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: CreateTransactionRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_provider),
) -> dict[str, object]:
    try:
        return PortfolioService(db, provider).create_transaction(user_id=user_id, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: str,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_provider),
) -> Response:
    try:
        PortfolioService(db, provider).delete_transaction(user_id=user_id, transaction_id=transaction_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
