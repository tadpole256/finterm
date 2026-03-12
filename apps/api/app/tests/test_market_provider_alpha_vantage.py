from __future__ import annotations

import pytest

from app.services.market_provider import AlphaVantageMarketDataProvider, provider_from_name


def test_factory_requires_alpha_vantage_key() -> None:
    with pytest.raises(ValueError):
        provider_from_name("alpha_vantage")


def test_alpha_vantage_quote_parsing(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = AlphaVantageMarketDataProvider(api_key="demo-key")

    def fake_request(params: dict[str, str]) -> dict[str, object]:
        assert params["function"] == "GLOBAL_QUOTE"
        assert params["symbol"] == "AAPL"
        return {
            "Global Quote": {
                "01. symbol": "AAPL",
                "05. price": "190.12",
                "06. volume": "1234000",
                "09. change": "1.45",
                "10. change percent": "0.768%",
            }
        }

    monkeypatch.setattr(provider, "_request", fake_request)

    quotes = provider.get_quotes(["AAPL"])
    assert len(quotes) == 1
    assert quotes[0].symbol == "AAPL"
    assert quotes[0].price == 190.12
    assert quotes[0].change_percent == 0.768


def test_alpha_vantage_daily_bars_parsing(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = AlphaVantageMarketDataProvider(api_key="demo-key")

    def fake_request(params: dict[str, str]) -> dict[str, object]:
        assert params["function"] == "TIME_SERIES_DAILY_ADJUSTED"
        return {
            "Time Series (Daily)": {
                "2026-03-10": {
                    "1. open": "101.0",
                    "2. high": "102.0",
                    "3. low": "99.5",
                    "4. close": "101.5",
                    "6. volume": "1100000",
                },
                "2026-03-11": {
                    "1. open": "101.6",
                    "2. high": "103.0",
                    "3. low": "100.1",
                    "4. close": "102.9",
                    "6. volume": "1300000",
                },
                "2026-03-12": {
                    "1. open": "103.1",
                    "2. high": "104.4",
                    "3. low": "102.5",
                    "4. close": "104.0",
                    "6. volume": "1400000",
                },
            }
        }

    monkeypatch.setattr(provider, "_request", fake_request)

    bars = provider.get_historical_bars("AAPL", timeframe="1M", points=2)
    assert len(bars) == 2
    assert bars[0].ts < bars[1].ts
    assert bars[0].close == 102.9
    assert bars[1].close == 104.0


def test_alpha_vantage_instrument_overview_parsing(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = AlphaVantageMarketDataProvider(api_key="demo-key")

    def fake_request(params: dict[str, str]) -> dict[str, object]:
        assert params["function"] == "OVERVIEW"
        assert params["symbol"] == "TSLA"
        return {
            "Symbol": "TSLA",
            "Name": "Tesla Inc",
            "Exchange": "NASDAQ",
            "Sector": "Consumer Cyclical",
            "Industry": "Auto Manufacturers",
            "MarketCapitalization": "650000000000",
        }

    monkeypatch.setattr(provider, "_request", fake_request)

    instrument = provider.get_instrument("TSLA")
    assert instrument is not None
    assert instrument.symbol == "TSLA"
    assert instrument.exchange == "NASDAQ"
    assert instrument.market_cap == 650000000000.0
