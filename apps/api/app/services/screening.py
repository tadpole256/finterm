from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Instrument, WatchlistItem
from app.services.market_provider import MarketDataProvider


@dataclass(slots=True)
class ScreenerFilters:
    price_min: float | None = None
    price_max: float | None = None
    market_cap_min: float | None = None
    market_cap_max: float | None = None
    change_percent_min: float | None = None
    change_percent_max: float | None = None
    sector: str | None = None
    watchlist_id: str | None = None
    tag: str | None = None


class ScreenerService:
    def __init__(self, db: Session, provider: MarketDataProvider) -> None:
        self.db = db
        self.provider = provider

    def run(self, filters: ScreenerFilters) -> list[dict[str, object]]:
        instruments = self.db.execute(select(Instrument).order_by(Instrument.symbol.asc())).scalars().all()
        quotes = {quote.symbol: quote for quote in self.provider.get_quotes([item.symbol for item in instruments])}

        allowed_symbols: set[str] | None = None
        if filters.watchlist_id:
            item_rows = self.db.execute(
                select(Instrument.symbol, WatchlistItem.tags)
                .join(WatchlistItem, WatchlistItem.instrument_id == Instrument.id)
                .where(WatchlistItem.watchlist_id == filters.watchlist_id)
            ).all()
            if filters.tag:
                allowed_symbols = {
                    symbol
                    for symbol, tags in item_rows
                    if isinstance(tags, list) and filters.tag in tags
                }
            else:
                allowed_symbols = {symbol for symbol, _ in item_rows}

        results: list[dict[str, object]] = []
        for instrument in instruments:
            quote = quotes.get(instrument.symbol)
            if quote is None:
                continue

            if filters.price_min is not None and quote.price < filters.price_min:
                continue
            if filters.price_max is not None and quote.price > filters.price_max:
                continue
            if filters.change_percent_min is not None and quote.change_percent < filters.change_percent_min:
                continue
            if filters.change_percent_max is not None and quote.change_percent > filters.change_percent_max:
                continue

            market_cap = float(instrument.market_cap) if instrument.market_cap is not None else None
            if filters.market_cap_min is not None and (market_cap is None or market_cap < filters.market_cap_min):
                continue
            if filters.market_cap_max is not None and (market_cap is None or market_cap > filters.market_cap_max):
                continue

            if filters.sector and instrument.sector != filters.sector:
                continue

            if allowed_symbols is not None and instrument.symbol not in allowed_symbols:
                continue

            results.append(
                {
                    "symbol": instrument.symbol,
                    "name": instrument.name,
                    "sector": instrument.sector,
                    "market_cap": market_cap,
                    "price": quote.price,
                    "change_percent": quote.change_percent,
                    "volume": quote.volume,
                }
            )

        return results
