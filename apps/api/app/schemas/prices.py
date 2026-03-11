from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import FreshnessEnvelope


class BarPoint(BaseModel):
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class IndicatorPoint(BaseModel):
    ts: datetime
    value: float | None


class MacdPoint(BaseModel):
    ts: datetime
    macd: float | None
    signal: float | None
    histogram: float | None


class IndicatorsResponse(BaseModel):
    sma20: list[IndicatorPoint]
    sma50: list[IndicatorPoint]
    ema20: list[IndicatorPoint]
    rsi14: list[IndicatorPoint]
    macd: list[MacdPoint]


class HistoricalBarsResponse(FreshnessEnvelope):
    symbol: str
    timeframe: str
    bars: list[BarPoint]
