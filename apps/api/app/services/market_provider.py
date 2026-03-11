from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from random import Random
from typing import Protocol


@dataclass(slots=True)
class ProviderMeta:
    source_provider: str
    as_of: datetime
    delay_seconds: int
    freshness_status: str

    @property
    def is_stale(self) -> bool:
        return self.freshness_status != "fresh"


@dataclass(slots=True)
class Quote:
    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    volume: float | None


@dataclass(slots=True)
class Bar:
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(slots=True)
class InstrumentInfo:
    symbol: str
    name: str
    exchange: str
    sector: str | None
    industry: str | None
    market_cap: float | None


@dataclass(slots=True)
class MacroEventInfo:
    id: str
    title: str
    scheduled_at: datetime
    impact: str
    actual: str | None
    forecast: str | None


class MarketDataProvider(Protocol):
    def provider_meta(self) -> ProviderMeta: ...

    def list_market_snapshot(self) -> list[Quote]: ...

    def get_quotes(self, symbols: list[str]) -> list[Quote]: ...

    def get_movers(self) -> tuple[list[Quote], list[Quote]]: ...

    def get_historical_bars(self, symbol: str, timeframe: str, points: int = 180) -> list[Bar]: ...

    def get_macro_events(self) -> list[MacroEventInfo]: ...

    def search_instruments(self, query: str) -> list[InstrumentInfo]: ...

    def get_instrument(self, symbol: str) -> InstrumentInfo | None: ...


class MockMarketDataProvider(MarketDataProvider):
    def __init__(self) -> None:
        fixture_dir = Path(__file__).resolve().parents[1] / "fixtures"
        self._instruments = json.loads((fixture_dir / "instruments.json").read_text())
        self._quotes = json.loads((fixture_dir / "quotes.json").read_text())
        self._movers = json.loads((fixture_dir / "movers.json").read_text())
        self._macro_events = json.loads((fixture_dir / "macro_events.json").read_text())

        self._instrument_by_symbol = {row["symbol"]: row for row in self._instruments}
        self._quote_by_symbol = {row["symbol"]: row for row in self._quotes}

    def provider_meta(self) -> ProviderMeta:
        return ProviderMeta(
            source_provider="mock",
            as_of=datetime.now(UTC),
            delay_seconds=900,
            freshness_status="stale",
        )

    def list_market_snapshot(self) -> list[Quote]:
        symbols = ["SPY", "QQQ", "IWM", "XLF"]
        return self.get_quotes(symbols)

    def get_quotes(self, symbols: list[str]) -> list[Quote]:
        quotes: list[Quote] = []
        for symbol in symbols:
            quote_row = self._quote_by_symbol.get(symbol)
            instrument = self._instrument_by_symbol.get(symbol)
            if quote_row is None:
                continue
            quotes.append(
                Quote(
                    symbol=symbol,
                    name=(instrument or {}).get("name", symbol),
                    price=float(quote_row["price"]),
                    change=float(quote_row["change"]),
                    change_percent=float(quote_row["change_percent"]),
                    volume=float(quote_row["volume"]) if quote_row.get("volume") else None,
                )
            )
        return quotes

    def get_movers(self) -> tuple[list[Quote], list[Quote]]:
        def _to_quote(payload: dict[str, float | str | None]) -> Quote:
            symbol = str(payload["symbol"])
            raw_price = payload.get("price")
            raw_change = payload.get("change")
            raw_change_percent = payload.get("change_percent")
            raw_volume = payload.get("volume")

            price = float(raw_price) if isinstance(raw_price, int | float | str) else 0.0
            change = float(raw_change) if isinstance(raw_change, int | float | str) else 0.0
            change_percent = (
                float(raw_change_percent)
                if isinstance(raw_change_percent, int | float | str)
                else 0.0
            )
            volume = float(raw_volume) if isinstance(raw_volume, int | float | str) else None
            return Quote(
                symbol=symbol,
                name=self._instrument_by_symbol.get(symbol, {}).get("name", symbol),
                price=price,
                change=change,
                change_percent=change_percent,
                volume=volume,
            )

        gainers = [_to_quote(row) for row in self._movers["gainers"]]
        losers = [_to_quote(row) for row in self._movers["losers"]]
        return gainers, losers

    def get_historical_bars(self, symbol: str, timeframe: str, points: int = 180) -> list[Bar]:
        quote = self._quote_by_symbol.get(symbol)
        if quote is None:
            return []

        base_price = float(quote["price"])
        seed = sum(ord(char) for char in symbol)
        randomizer = Random(seed)

        interval = {
            "1M": timedelta(days=1),
            "3M": timedelta(days=1),
            "6M": timedelta(days=1),
            "1Y": timedelta(days=1),
            "5D": timedelta(minutes=30),
            "1D": timedelta(minutes=5),
        }.get(timeframe, timedelta(days=1))

        bars: list[Bar] = []
        current = base_price * 0.82
        now = datetime.now(UTC)

        for index in range(points):
            ts = now - interval * (points - index)
            drift = randomizer.uniform(-0.015, 0.017)
            open_price = current
            close_price = max(0.01, open_price * (1 + drift))
            high_price = max(open_price, close_price) * (1 + randomizer.uniform(0.001, 0.013))
            low_price = min(open_price, close_price) * (1 - randomizer.uniform(0.001, 0.012))
            volume = abs(randomizer.gauss(42_000_000, 9_500_000))

            bars.append(
                Bar(
                    ts=ts,
                    open=round(open_price, 4),
                    high=round(high_price, 4),
                    low=round(low_price, 4),
                    close=round(close_price, 4),
                    volume=round(volume, 2),
                )
            )
            current = close_price

        return bars

    def get_macro_events(self) -> list[MacroEventInfo]:
        events: list[MacroEventInfo] = []
        for row in self._macro_events:
            events.append(
                MacroEventInfo(
                    id=f"macro-{row['title']}",
                    title=str(row["title"]),
                    scheduled_at=datetime.fromisoformat(str(row["scheduled_at"]).replace("Z", "+00:00")),
                    impact=str(row["impact"]),
                    actual=str(row["actual"]) if row.get("actual") is not None else None,
                    forecast=str(row["forecast"]) if row.get("forecast") is not None else None,
                )
            )
        return events

    def search_instruments(self, query: str) -> list[InstrumentInfo]:
        normalized = query.lower()
        matches = [
            row
            for row in self._instruments
            if normalized in row["symbol"].lower() or normalized in row["name"].lower()
        ]
        return [self._instrument_info(row) for row in matches[:25]]

    def get_instrument(self, symbol: str) -> InstrumentInfo | None:
        row = self._instrument_by_symbol.get(symbol.upper())
        if row is None:
            return None
        return self._instrument_info(row)

    def _instrument_info(self, row: dict[str, str | float | None]) -> InstrumentInfo:
        market_cap_value = row.get("market_cap")
        return InstrumentInfo(
            symbol=str(row["symbol"]),
            name=str(row["name"]),
            exchange=str(row["exchange"]),
            sector=str(row["sector"]) if row.get("sector") else None,
            industry=str(row["industry"]) if row.get("industry") else None,
            market_cap=float(market_cap_value) if market_cap_value is not None else None,
        )


def provider_from_name(name: str) -> MarketDataProvider:
    normalized = name.lower().strip()
    if normalized in {"mock", "delayed", "premium"}:
        return MockMarketDataProvider()
    raise ValueError(f"Unsupported market data provider '{name}'")
