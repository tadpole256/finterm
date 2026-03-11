from datetime import UTC, datetime, timedelta

from app.services.indicators import ema, macd, rsi, sma
from app.services.market_provider import Bar


def build_bars(count: int) -> list[Bar]:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    bars: list[Bar] = []
    price = 100.0
    for index in range(count):
        price += 0.5
        bars.append(
            Bar(
                ts=start + timedelta(days=index),
                open=price - 0.2,
                high=price + 0.6,
                low=price - 0.8,
                close=price,
                volume=1_000_000 + index * 10,
            )
        )
    return bars


def test_indicator_lengths_and_null_windows() -> None:
    bars = build_bars(80)

    sma20 = sma(bars, 20)
    ema20 = ema(bars, 20)
    rsi14 = rsi(bars, 14)
    macd_values = macd(bars)

    assert len(sma20) == 80
    assert len(ema20) == 80
    assert len(rsi14) == 80
    assert len(macd_values) == 80
    assert sma20[18].value is None
    assert sma20[19].value is not None
    assert ema20[19].value is not None
