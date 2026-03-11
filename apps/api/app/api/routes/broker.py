from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_broker_provider, get_provider, get_user_id
from app.db.session import get_db
from app.schemas.broker import (
    BrokerAccountDetail,
    BrokerReconciliationResponse,
    BrokerSyncResponse,
)
from app.services.broker import BrokerService
from app.services.broker_provider import BrokerProvider
from app.services.market_provider import MarketDataProvider

router = APIRouter(prefix="/broker", tags=["broker"])


@router.get("/accounts", response_model=list[BrokerAccountDetail])
def list_broker_accounts(
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
    broker_provider: BrokerProvider = Depends(get_broker_provider),
    market_provider: MarketDataProvider = Depends(get_provider),
) -> list[dict[str, object]]:
    return BrokerService(db, broker_provider, market_provider).list_account_details(user_id=user_id)


@router.post("/sync", response_model=BrokerSyncResponse, status_code=status.HTTP_201_CREATED)
def run_broker_sync(
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
    broker_provider: BrokerProvider = Depends(get_broker_provider),
    market_provider: MarketDataProvider = Depends(get_provider),
) -> dict[str, object]:
    try:
        return BrokerService(db, broker_provider, market_provider).sync(user_id=user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/reconcile", response_model=BrokerReconciliationResponse)
def get_broker_reconciliation(
    portfolio_id: str | None = Query(default=None),
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
    broker_provider: BrokerProvider = Depends(get_broker_provider),
    market_provider: MarketDataProvider = Depends(get_provider),
) -> dict[str, object]:
    try:
        return BrokerService(db, broker_provider, market_provider).reconcile(
            user_id=user_id,
            portfolio_id=portfolio_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
