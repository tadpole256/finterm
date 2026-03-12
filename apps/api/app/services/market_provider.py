from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from random import Random
from typing import Any, Protocol

import httpx

LOGGER = logging.getLogger(__name__)


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


class AlphaVantageMarketDataProvider(MarketDataProvider):
    _DEFAULT_BASE_URL = "https://www.alphavantage.co/query"
    _MARKET_SNAPSHOT_SYMBOLS = ("SPY", "QQQ", "IWM", "XLF")
    _QUOTE_CACHE_TTL = timedelta(minutes=15)
    _BARS_CACHE_TTL = timedelta(minutes=30)
    _INSTRUMENT_CACHE_TTL = timedelta(hours=6)
    _TIMEFRAME_WINDOWS: dict[str, int] = {
        "1D": 20,
        "5D": 30,
        "1M": 22,
        "3M": 66,
        "6M": 132,
        "1Y": 252,
    }

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
    ) -> None:
        normalized_key = api_key.strip()
        if not normalized_key or normalized_key.lower() in {"replace_with_free_key", "your_api_key"}:
            raise ValueError(
                "ALPHA_VANTAGE_API_KEY must be set when MARKET_DATA_PROVIDER=alpha_vantage."
            )

        fixture_dir = Path(__file__).resolve().parents[1] / "fixtures"
        self._instruments = json.loads((fixture_dir / "instruments.json").read_text())
        self._macro_events = json.loads((fixture_dir / "macro_events.json").read_text())
        self._instrument_by_symbol = {row["symbol"]: row for row in self._instruments}

        self.api_key = normalized_key
        self.base_url = (base_url or self._DEFAULT_BASE_URL).strip()
        self._client = httpx.Client(timeout=15.0)

        self._quote_cache: dict[str, tuple[datetime, Quote]] = {}
        self._bars_cache: dict[tuple[str, str, int], tuple[datetime, list[Bar]]] = {}
        self._instrument_cache: dict[str, tuple[datetime, InstrumentInfo]] = {}

    def provider_meta(self) -> ProviderMeta:
        return ProviderMeta(
            source_provider="alpha_vantage",
            as_of=datetime.now(UTC),
            delay_seconds=86_400,
            freshness_status="stale",
        )

    def list_market_snapshot(self) -> list[Quote]:
        symbols = [
            symbol
            for symbol in self._MARKET_SNAPSHOT_SYMBOLS
            if symbol in self._instrument_by_symbol
        ]
        if not symbols:
            symbols = list(self._instrument_by_symbol.keys())[:4]
        return self.get_quotes(symbols)

    def get_quotes(self, symbols: list[str]) -> list[Quote]:
        normalized_symbols = self._normalize_symbols(symbols)
        quote_by_symbol: dict[str, Quote] = {}

        for symbol in normalized_symbols:
            cached_quote = self._get_cached_quote(symbol)
            if cached_quote is not None:
                quote_by_symbol[symbol] = cached_quote
                continue

            fresh_quote = self._fetch_quote(symbol)
            if fresh_quote is None:
                continue
            quote_by_symbol[symbol] = fresh_quote
            self._quote_cache[symbol] = (datetime.now(UTC) + self._QUOTE_CACHE_TTL, fresh_quote)

        return [quote_by_symbol[symbol] for symbol in normalized_symbols if symbol in quote_by_symbol]

    def get_movers(self) -> tuple[list[Quote], list[Quote]]:
        try:
            payload = self._request({"function": "TOP_GAINERS_LOSERS"})
            gainers = self._parse_top_movers(payload.get("top_gainers"))
            losers = self._parse_top_movers(payload.get("top_losers"))
            if gainers or losers:
                return gainers[:5], losers[:5]
        except RuntimeError as exc:
            LOGGER.warning("Alpha Vantage top movers request failed: %s", exc)

        fallback_quotes = self.get_quotes(list(self._instrument_by_symbol.keys()))
        if not fallback_quotes:
            return [], []
        gainers = sorted(fallback_quotes, key=lambda item: item.change_percent, reverse=True)[:5]
        losers = sorted(fallback_quotes, key=lambda item: item.change_percent)[:5]
        return gainers, losers

    def get_historical_bars(self, symbol: str, timeframe: str, points: int = 180) -> list[Bar]:
        normalized_symbol = symbol.strip().upper()
        normalized_timeframe = timeframe.strip().upper()
        cache_key = (normalized_symbol, normalized_timeframe, points)
        cached = self._bars_cache.get(cache_key)
        now = datetime.now(UTC)
        if cached is not None and cached[0] >= now:
            return cached[1]

        bars = self._fetch_daily_bars(normalized_symbol, normalized_timeframe, points)
        if bars:
            self._bars_cache[cache_key] = (now + self._BARS_CACHE_TTL, bars)
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
        normalized_query = query.strip().lower()
        local_matches = [
            self._instrument_info(row)
            for row in self._instruments
            if normalized_query in row["symbol"].lower() or normalized_query in row["name"].lower()
        ]

        if not normalized_query:
            return local_matches[:25]

        try:
            payload = self._request({"function": "SYMBOL_SEARCH", "keywords": query.strip()})
        except RuntimeError as exc:
            LOGGER.warning("Alpha Vantage symbol search failed: %s", exc)
            return local_matches[:25]

        raw_matches = payload.get("bestMatches")
        if not isinstance(raw_matches, list):
            return local_matches[:25]

        results: list[InstrumentInfo] = []
        seen_symbols: set[str] = set()
        for raw_match in raw_matches:
            if not isinstance(raw_match, dict):
                continue

            symbol = str(raw_match.get("1. symbol") or "").strip().upper()
            if not symbol or symbol in seen_symbols:
                continue
            seen_symbols.add(symbol)

            local_info = self._instrument_by_symbol.get(symbol)
            name = str(raw_match.get("2. name") or (local_info or {}).get("name") or symbol)
            exchange = str(raw_match.get("4. region") or (local_info or {}).get("exchange") or "UNKNOWN")
            sector = str(local_info["sector"]) if local_info and local_info.get("sector") else None
            industry = str(local_info["industry"]) if local_info and local_info.get("industry") else None
            market_cap = (
                float(local_info["market_cap"])
                if local_info and local_info.get("market_cap") is not None
                else None
            )
            results.append(
                InstrumentInfo(
                    symbol=symbol,
                    name=name,
                    exchange=exchange,
                    sector=sector,
                    industry=industry,
                    market_cap=market_cap,
                )
            )
            if len(results) >= 25:
                break

        return results or local_matches[:25]

    def get_instrument(self, symbol: str) -> InstrumentInfo | None:
        normalized_symbol = symbol.strip().upper()
        if not normalized_symbol:
            return None

        cached_instrument = self._get_cached_instrument(normalized_symbol)
        if cached_instrument is not None:
            return cached_instrument

        local_info = self._instrument_by_symbol.get(normalized_symbol)
        if local_info is not None:
            instrument = self._instrument_info(local_info)
            self._instrument_cache[normalized_symbol] = (
                datetime.now(UTC) + self._INSTRUMENT_CACHE_TTL,
                instrument,
            )
            return instrument

        try:
            payload = self._request({"function": "OVERVIEW", "symbol": normalized_symbol})
        except RuntimeError as exc:
            LOGGER.warning("Alpha Vantage overview request failed: %s", exc)
            return self._find_exact_from_search(normalized_symbol)

        payload_symbol = str(payload.get("Symbol") or "").strip().upper()
        if payload_symbol:
            instrument = InstrumentInfo(
                symbol=payload_symbol,
                name=str(payload.get("Name") or payload_symbol),
                exchange=str(payload.get("Exchange") or "UNKNOWN"),
                sector=str(payload.get("Sector")) if payload.get("Sector") else None,
                industry=str(payload.get("Industry")) if payload.get("Industry") else None,
                market_cap=_parse_float(payload.get("MarketCapitalization")),
            )
            self._instrument_cache[normalized_symbol] = (
                datetime.now(UTC) + self._INSTRUMENT_CACHE_TTL,
                instrument,
            )
            return instrument

        return self._find_exact_from_search(normalized_symbol)

    def _normalize_symbols(self, symbols: list[str]) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []
        for symbol in symbols:
            normalized = symbol.strip().upper()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            ordered.append(normalized)
        return ordered

    def _get_cached_quote(self, symbol: str) -> Quote | None:
        cached = self._quote_cache.get(symbol)
        if cached is None:
            return None
        if cached[0] < datetime.now(UTC):
            self._quote_cache.pop(symbol, None)
            return None
        return cached[1]

    def _get_cached_instrument(self, symbol: str) -> InstrumentInfo | None:
        cached = self._instrument_cache.get(symbol)
        if cached is None:
            return None
        if cached[0] < datetime.now(UTC):
            self._instrument_cache.pop(symbol, None)
            return None
        return cached[1]

    def _fetch_quote(self, symbol: str) -> Quote | None:
        try:
            payload = self._request({"function": "GLOBAL_QUOTE", "symbol": symbol})
        except RuntimeError as exc:
            LOGGER.warning("Alpha Vantage quote request failed for %s: %s", symbol, exc)
            return None

        raw_quote = payload.get("Global Quote")
        if not isinstance(raw_quote, dict):
            return None

        parsed_symbol = str(raw_quote.get("01. symbol") or symbol).strip().upper()
        price = _parse_float(raw_quote.get("05. price"))
        if price is None:
            return None

        change = _parse_float(raw_quote.get("09. change")) or 0.0
        change_percent = _parse_float(raw_quote.get("10. change percent")) or 0.0
        volume = _parse_float(raw_quote.get("06. volume"))

        known_name = self._instrument_by_symbol.get(parsed_symbol, {}).get("name")
        return Quote(
            symbol=parsed_symbol,
            name=str(known_name or parsed_symbol),
            price=price,
            change=change,
            change_percent=change_percent,
            volume=volume,
        )

    def _fetch_daily_bars(self, symbol: str, timeframe: str, points: int) -> list[Bar]:
        try:
            payload = self._request(
                {
                    "function": "TIME_SERIES_DAILY_ADJUSTED",
                    "symbol": symbol,
                    "outputsize": "full",
                }
            )
        except RuntimeError as exc:
            LOGGER.warning("Alpha Vantage bars request failed for %s: %s", symbol, exc)
            return []

        raw_series = payload.get("Time Series (Daily)")
        if not isinstance(raw_series, dict):
            return []

        bars: list[Bar] = []
        for raw_ts, raw_row in raw_series.items():
            if not isinstance(raw_ts, str) or not isinstance(raw_row, dict):
                continue
            try:
                ts = datetime.strptime(raw_ts, "%Y-%m-%d").replace(tzinfo=UTC)
            except ValueError:
                continue

            open_price = _parse_float(raw_row.get("1. open"))
            high_price = _parse_float(raw_row.get("2. high"))
            low_price = _parse_float(raw_row.get("3. low"))
            close_price = _parse_float(raw_row.get("4. close"))
            volume = _parse_float(raw_row.get("6. volume"))

            if (
                open_price is None
                or high_price is None
                or low_price is None
                or close_price is None
                or volume is None
            ):
                continue

            bars.append(
                Bar(
                    ts=ts,
                    open=open_price,
                    high=high_price,
                    low=low_price,
                    close=close_price,
                    volume=volume,
                )
            )

        bars.sort(key=lambda item: item.ts)
        if not bars:
            return []

        window = self._TIMEFRAME_WINDOWS.get(timeframe, points)
        capped = min(max(window, 1), max(points, 1), len(bars))
        return bars[-capped:]

    def _parse_top_movers(self, raw_items: object) -> list[Quote]:
        if not isinstance(raw_items, list):
            return []

        quotes: list[Quote] = []
        for raw_item in raw_items:
            if not isinstance(raw_item, dict):
                continue
            symbol = str(raw_item.get("ticker") or "").strip().upper()
            if not symbol:
                continue
            price = _parse_float(raw_item.get("price"))
            if price is None:
                continue
            quotes.append(
                Quote(
                    symbol=symbol,
                    name=str(self._instrument_by_symbol.get(symbol, {}).get("name", symbol)),
                    price=price,
                    change=_parse_float(raw_item.get("change_amount")) or 0.0,
                    change_percent=_parse_float(raw_item.get("change_percentage")) or 0.0,
                    volume=_parse_float(raw_item.get("volume")),
                )
            )
        return quotes

    def _find_exact_from_search(self, symbol: str) -> InstrumentInfo | None:
        for candidate in self.search_instruments(symbol):
            if candidate.symbol == symbol:
                self._instrument_cache[symbol] = (
                    datetime.now(UTC) + self._INSTRUMENT_CACHE_TTL,
                    candidate,
                )
                return candidate
        return None

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

    def _request(self, params: dict[str, str]) -> dict[str, Any]:
        try:
            response = self._client.get(self.base_url, params={**params, "apikey": self.api_key})
            response.raise_for_status()
            payload = response.json()
        except (httpx.RequestError, httpx.HTTPStatusError) as exc:
            raise RuntimeError(f"Alpha Vantage request failed: {exc}") from exc
        except ValueError as exc:
            raise RuntimeError("Alpha Vantage returned an invalid JSON response.") from exc

        if not isinstance(payload, dict):
            raise RuntimeError("Unexpected response payload from Alpha Vantage.")

        error_message = payload.get("Error Message")
        if isinstance(error_message, str) and error_message:
            raise RuntimeError(error_message)

        informational_message = payload.get("Note") or payload.get("Information")
        if isinstance(informational_message, str) and informational_message:
            raise RuntimeError(informational_message)

        return payload


def _parse_float(raw_value: object) -> float | None:
    if isinstance(raw_value, int | float):
        return float(raw_value)
    if not isinstance(raw_value, str):
        return None

    cleaned = raw_value.strip().replace(",", "").replace("%", "")
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def provider_from_name(
    name: str,
    *,
    alpha_vantage_api_key: str | None = None,
    alpha_vantage_base_url: str | None = None,
) -> MarketDataProvider:
    normalized = name.lower().strip()
    if normalized in {"mock", "delayed", "premium"}:
        return MockMarketDataProvider()
    if normalized in {"alpha_vantage", "alphavantage", "av"}:
        return AlphaVantageMarketDataProvider(
            api_key=alpha_vantage_api_key or "",
            base_url=alpha_vantage_base_url,
        )
    raise ValueError(f"Unsupported market data provider '{name}'")
