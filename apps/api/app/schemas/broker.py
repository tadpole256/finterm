from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class BrokerAccountView(BaseModel):
    id: str
    provider: str
    external_account_id: str
    account_name: str
    account_type: str
    base_currency: str
    status: str
    last_synced_at: datetime | None
    account_meta: dict[str, Any]
    position_count: int
    total_market_value: float


class BrokerPositionView(BaseModel):
    symbol: str
    quantity: float
    avg_cost: float | None
    market_price: float | None
    market_value: float | None
    as_of: datetime


class BrokerAccountDetail(BrokerAccountView):
    positions: list[BrokerPositionView]


class BrokerSyncResponse(BaseModel):
    run_id: str
    provider: str
    status: str
    fetched_accounts: int
    fetched_positions: int
    started_at: datetime
    completed_at: datetime | None
    message: str


class BrokerPositionDelta(BaseModel):
    symbol: str
    local_quantity: float
    broker_quantity: float
    quantity_delta: float
    local_market_value: float | None
    broker_market_value: float | None


class BrokerReconciliationResponse(BaseModel):
    as_of: datetime
    summary: dict[str, int]
    only_local: list[str]
    only_broker: list[str]
    quantity_mismatches: list[BrokerPositionDelta]
    open_exception_count: int = 0


class ReconciliationExceptionView(BaseModel):
    id: str
    symbol: str
    issue_type: str
    severity: str
    status: str
    local_quantity: float | None
    broker_quantity: float | None
    local_market_value: float | None
    broker_market_value: float | None
    detected_at: datetime
    last_seen_at: datetime
    resolved_at: datetime | None
    resolution_note: str | None
    details: dict[str, Any]


class ResolveReconciliationExceptionRequest(BaseModel):
    resolution_note: str | None = Field(default=None, max_length=1000)


class BrokerCapabilitiesView(BaseModel):
    provider: str
    supports_positions: bool
    supports_order_preview: bool
    supports_order_submission: bool
    supports_reconciliation: bool
    requires_auth: bool
    trading_enabled: bool
    can_submit_orders: bool
    restrictions: list[str]


class BrokerSessionView(BaseModel):
    provider: str
    connected: bool
    auth_state: str
    last_refreshed_at: datetime
    expires_at: datetime | None


class BrokerCapabilityResponse(BaseModel):
    capabilities: BrokerCapabilitiesView
    session: BrokerSessionView


class BrokerOrderPreviewRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=24)
    side: Literal["buy", "sell"]
    order_type: Literal["market", "limit"] = "market"
    quantity: float = Field(gt=0)
    limit_price: float | None = Field(default=None, gt=0)


class BrokerOrderPreviewResponse(BaseModel):
    provider: str
    symbol: str
    side: str
    order_type: str
    quantity: float
    reference_price: float
    estimated_notional: float
    estimated_fees: float
    estimated_total_cash: float
    can_submit: bool
    restrictions: list[str]
    warnings: list[str]


class BrokerOrderEventView(BaseModel):
    id: str
    broker_account_id: str | None
    external_order_id: str
    symbol: str
    side: str
    order_type: str
    status: str
    quantity: float
    limit_price: float | None
    filled_quantity: float
    avg_fill_price: float | None
    submitted_at: datetime
    status_updated_at: datetime | None
    event_payload: dict[str, Any]


class CreateBrokerOrderEventRequest(BaseModel):
    broker_account_id: str | None = None
    external_order_id: str = Field(min_length=1, max_length=120)
    symbol: str = Field(min_length=1, max_length=24)
    side: Literal["buy", "sell"]
    order_type: Literal["market", "limit"] = "market"
    status: str = Field(default="filled", min_length=1, max_length=24)
    quantity: float = Field(gt=0)
    limit_price: float | None = Field(default=None, gt=0)
    filled_quantity: float = Field(default=0, ge=0)
    avg_fill_price: float | None = Field(default=None, gt=0)
    status_updated_at: datetime | None = None
    event_payload: dict[str, Any] = Field(default_factory=dict)
    create_journal_entry: bool = True
