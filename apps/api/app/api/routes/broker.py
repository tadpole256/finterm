from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import (
    get_broker_provider,
    get_broker_trading_enabled,
    get_provider,
    get_user_id,
)
from app.db.session import get_db
from app.schemas.broker import (
    BrokerAccountDetail,
    BrokerCapabilityResponse,
    BrokerOrderEventView,
    BrokerOrderPreviewRequest,
    BrokerOrderPreviewResponse,
    BrokerReconciliationResponse,
    BrokerSyncResponse,
    CreateBrokerOrderEventRequest,
    ReconciliationExceptionView,
    ResolveReconciliationExceptionRequest,
)
from app.services.broker import BrokerService
from app.services.broker_provider import BrokerProvider
from app.services.market_provider import MarketDataProvider

router = APIRouter(prefix="/broker", tags=["broker"])


def _service(
    db: Session,
    broker_provider: BrokerProvider,
    market_provider: MarketDataProvider,
    trading_enabled: bool,
) -> BrokerService:
    return BrokerService(
        db,
        broker_provider,
        market_provider,
        trading_enabled=trading_enabled,
    )


@router.get("/capabilities", response_model=BrokerCapabilityResponse)
def get_broker_capabilities(
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
    broker_provider: BrokerProvider = Depends(get_broker_provider),
    market_provider: MarketDataProvider = Depends(get_provider),
    trading_enabled: bool = Depends(get_broker_trading_enabled),
) -> dict[str, object]:
    return _service(db, broker_provider, market_provider, trading_enabled).capabilities(user_id=user_id)


@router.get("/accounts", response_model=list[BrokerAccountDetail])
def list_broker_accounts(
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
    broker_provider: BrokerProvider = Depends(get_broker_provider),
    market_provider: MarketDataProvider = Depends(get_provider),
    trading_enabled: bool = Depends(get_broker_trading_enabled),
) -> list[dict[str, object]]:
    return _service(db, broker_provider, market_provider, trading_enabled).list_account_details(
        user_id=user_id
    )


@router.post("/sync", response_model=BrokerSyncResponse, status_code=status.HTTP_201_CREATED)
def run_broker_sync(
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
    broker_provider: BrokerProvider = Depends(get_broker_provider),
    market_provider: MarketDataProvider = Depends(get_provider),
    trading_enabled: bool = Depends(get_broker_trading_enabled),
) -> dict[str, object]:
    try:
        return _service(db, broker_provider, market_provider, trading_enabled).sync(user_id=user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/orders/preview", response_model=BrokerOrderPreviewResponse)
def preview_order(
    payload: BrokerOrderPreviewRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
    broker_provider: BrokerProvider = Depends(get_broker_provider),
    market_provider: MarketDataProvider = Depends(get_provider),
    trading_enabled: bool = Depends(get_broker_trading_enabled),
) -> dict[str, object]:
    try:
        return _service(db, broker_provider, market_provider, trading_enabled).preview_order(
            user_id=user_id,
            symbol=payload.symbol,
            side=payload.side,
            order_type=payload.order_type,
            quantity=payload.quantity,
            limit_price=payload.limit_price,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/order-events", response_model=BrokerOrderEventView, status_code=status.HTTP_201_CREATED)
def create_order_event(
    payload: CreateBrokerOrderEventRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
    broker_provider: BrokerProvider = Depends(get_broker_provider),
    market_provider: MarketDataProvider = Depends(get_provider),
    trading_enabled: bool = Depends(get_broker_trading_enabled),
) -> dict[str, object]:
    try:
        return _service(db, broker_provider, market_provider, trading_enabled).record_order_event(
            user_id=user_id,
            broker_account_id=payload.broker_account_id,
            external_order_id=payload.external_order_id,
            symbol=payload.symbol,
            side=payload.side,
            order_type=payload.order_type,
            status=payload.status,
            quantity=payload.quantity,
            limit_price=payload.limit_price,
            filled_quantity=payload.filled_quantity,
            avg_fill_price=payload.avg_fill_price,
            status_updated_at=payload.status_updated_at,
            event_payload=payload.event_payload,
            create_journal_entry=payload.create_journal_entry,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/order-events", response_model=list[BrokerOrderEventView])
def list_order_events(
    symbol: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=250),
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
    broker_provider: BrokerProvider = Depends(get_broker_provider),
    market_provider: MarketDataProvider = Depends(get_provider),
    trading_enabled: bool = Depends(get_broker_trading_enabled),
) -> list[dict[str, object]]:
    return _service(db, broker_provider, market_provider, trading_enabled).list_order_events(
        user_id=user_id,
        symbol=symbol,
        status=status_filter,
        limit=limit,
    )


@router.get("/reconcile", response_model=BrokerReconciliationResponse)
def get_broker_reconciliation(
    portfolio_id: str | None = Query(default=None),
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
    broker_provider: BrokerProvider = Depends(get_broker_provider),
    market_provider: MarketDataProvider = Depends(get_provider),
    trading_enabled: bool = Depends(get_broker_trading_enabled),
) -> dict[str, object]:
    try:
        return _service(db, broker_provider, market_provider, trading_enabled).reconcile(
            user_id=user_id,
            portfolio_id=portfolio_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/reconciliation-exceptions", response_model=list[ReconciliationExceptionView])
def list_reconciliation_exceptions(
    status_filter: str = Query(default="open", alias="status"),
    limit: int = Query(default=100, ge=1, le=300),
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
    broker_provider: BrokerProvider = Depends(get_broker_provider),
    market_provider: MarketDataProvider = Depends(get_provider),
    trading_enabled: bool = Depends(get_broker_trading_enabled),
) -> list[dict[str, object]]:
    return _service(db, broker_provider, market_provider, trading_enabled).list_reconciliation_exceptions(
        user_id=user_id,
        status_filter=status_filter,
        limit=limit,
    )


@router.patch(
    "/reconciliation-exceptions/{exception_id}/resolve",
    response_model=ReconciliationExceptionView,
)
def resolve_reconciliation_exception(
    exception_id: str,
    payload: ResolveReconciliationExceptionRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
    broker_provider: BrokerProvider = Depends(get_broker_provider),
    market_provider: MarketDataProvider = Depends(get_provider),
    trading_enabled: bool = Depends(get_broker_trading_enabled),
) -> dict[str, object]:
    try:
        return _service(db, broker_provider, market_provider, trading_enabled).resolve_reconciliation_exception(
            user_id=user_id,
            exception_id=exception_id,
            resolution_note=payload.resolution_note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
