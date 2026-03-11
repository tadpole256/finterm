from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class PortfolioHeader(BaseModel):
    id: str
    name: str
    base_currency: str


class PortfolioSummary(BaseModel):
    market_value: float
    cost_basis: float
    unrealized_pnl: float
    realized_pnl: float
    total_pnl: float
    position_count: int


class HoldingView(BaseModel):
    instrument_id: str
    symbol: str
    name: str
    sector: str | None
    quantity: float
    avg_cost: float
    last_price: float | None
    market_value: float | None
    cost_basis: float
    unrealized_pnl: float | None
    realized_pnl: float
    note_count: int
    active_thesis_count: int
    watchlists: list[str]


class ExposureItem(BaseModel):
    sector: str
    market_value: float
    weight: float


class PortfolioTransactionView(BaseModel):
    id: str
    symbol: str
    trade_date: datetime
    side: Literal["buy", "sell"]
    quantity: float
    price: float
    fees: float
    notional: float
    notes: str | None


class RiskTopPosition(BaseModel):
    symbol: str
    market_value: float
    weight: float


class RiskFactorExposure(BaseModel):
    factor: str
    exposure: float
    method: str


class ScenarioImpact(BaseModel):
    name: str
    estimated_pnl: float
    estimated_return: float
    assumptions: str


class PortfolioOverviewResponse(BaseModel):
    portfolio: PortfolioHeader
    as_of: datetime
    summary: PortfolioSummary
    holdings: list[HoldingView]
    exposures: list[ExposureItem]
    transactions: list[PortfolioTransactionView]


class PositionsResponse(BaseModel):
    portfolio: PortfolioHeader
    as_of: datetime
    holdings: list[HoldingView]


class TransactionsResponse(BaseModel):
    portfolio: PortfolioHeader
    transactions: list[PortfolioTransactionView]


class PortfolioRiskResponse(BaseModel):
    portfolio: PortfolioHeader
    as_of: datetime
    net_exposure: float
    gross_exposure: float
    concentration_hhi: float
    top_positions: list[RiskTopPosition]
    factor_exposures: list[RiskFactorExposure]
    scenarios: list[ScenarioImpact]


class CreateTransactionRequest(BaseModel):
    portfolio_id: str | None = None
    symbol: str = Field(min_length=1, max_length=24)
    trade_date: datetime | None = None
    side: Literal["buy", "sell"]
    quantity: float = Field(gt=0)
    price: float = Field(gt=0)
    fees: float = Field(default=0, ge=0)
    notes: str | None = Field(default=None, max_length=2000)
