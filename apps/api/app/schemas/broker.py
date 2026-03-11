from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


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
