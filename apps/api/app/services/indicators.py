from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.services.market_provider import Bar


@dataclass(slots=True)
class IndicatorPoint:
    ts: datetime
    value: float | None


@dataclass(slots=True)
class MacdPoint:
    ts: datetime
    macd: float | None
    signal: float | None
    histogram: float | None


def sma(bars: list[Bar], period: int) -> list[IndicatorPoint]:
    points: list[IndicatorPoint] = []
    closes = [bar.close for bar in bars]

    for index, bar in enumerate(bars):
        if index + 1 < period:
            points.append(IndicatorPoint(ts=bar.ts, value=None))
            continue
        window = closes[index + 1 - period : index + 1]
        points.append(IndicatorPoint(ts=bar.ts, value=round(sum(window) / period, 6)))

    return points


def ema(bars: list[Bar], period: int) -> list[IndicatorPoint]:
    if not bars:
        return []

    points: list[IndicatorPoint] = []
    multiplier = 2 / (period + 1)
    ema_value: float | None = None

    for index, bar in enumerate(bars):
        if index + 1 < period:
            points.append(IndicatorPoint(ts=bar.ts, value=None))
            continue

        if ema_value is None:
            seed = sum(candidate.close for candidate in bars[index + 1 - period : index + 1]) / period
            ema_value = seed
        else:
            ema_value = (bar.close - ema_value) * multiplier + ema_value

        points.append(IndicatorPoint(ts=bar.ts, value=round(ema_value, 6)))

    return points


def rsi(bars: list[Bar], period: int = 14) -> list[IndicatorPoint]:
    if len(bars) < period + 1:
        return [IndicatorPoint(ts=bar.ts, value=None) for bar in bars]

    deltas = [bars[idx].close - bars[idx - 1].close for idx in range(1, len(bars))]
    gains = [max(delta, 0.0) for delta in deltas]
    losses = [abs(min(delta, 0.0)) for delta in deltas]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    points: list[IndicatorPoint] = [IndicatorPoint(ts=bar.ts, value=None) for bar in bars]

    for idx in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[idx]) / period
        avg_loss = (avg_loss * (period - 1) + losses[idx]) / period

        if avg_loss == 0:
            value = 100.0
        else:
            rs = avg_gain / avg_loss
            value = 100 - (100 / (1 + rs))

        points[idx + 1].value = round(value, 6)

    return points


def macd(
    bars: list[Bar],
    short_period: int = 12,
    long_period: int = 26,
    signal_period: int = 9,
) -> list[MacdPoint]:
    ema_short = ema(bars, short_period)
    ema_long = ema(bars, long_period)

    macd_raw: list[float | None] = []
    for short, long in zip(ema_short, ema_long, strict=True):
        if short.value is None or long.value is None:
            macd_raw.append(None)
        else:
            macd_raw.append(short.value - long.value)

    signal_values: list[float | None] = []
    active_macd: list[float] = []

    for value in macd_raw:
        if value is None:
            signal_values.append(None)
            continue

        active_macd.append(value)
        if len(active_macd) < signal_period:
            signal_values.append(None)
            continue

        if len(active_macd) == signal_period:
            signal_values.append(sum(active_macd[-signal_period:]) / signal_period)
            continue

        previous_signal = signal_values[-1]
        assert previous_signal is not None
        multiplier = 2 / (signal_period + 1)
        next_signal = (value - previous_signal) * multiplier + previous_signal
        signal_values.append(next_signal)

    points: list[MacdPoint] = []
    for bar, macd_value, signal_value in zip(bars, macd_raw, signal_values, strict=True):
        histogram = None
        if macd_value is not None and signal_value is not None:
            histogram = macd_value - signal_value
        points.append(
            MacdPoint(
                ts=bar.ts,
                macd=round(macd_value, 6) if macd_value is not None else None,
                signal=round(signal_value, 6) if signal_value is not None else None,
                histogram=round(histogram, 6) if histogram is not None else None,
            )
        )

    return points
