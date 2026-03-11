from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Instrument, SavedScreen, Watchlist, WatchlistItem
from app.services.market_provider import MarketDataProvider


@dataclass(slots=True)
class ScreenerFilters:
    price_min: float | None = None
    price_max: float | None = None
    market_cap_min: float | None = None
    market_cap_max: float | None = None
    change_percent_min: float | None = None
    change_percent_max: float | None = None
    volume_min: float | None = None
    volume_max: float | None = None
    sector: str | None = None
    asset_type: str | None = None
    symbol_query: str | None = None
    watchlist_id: str | None = None
    tag: str | None = None
    sort_by: str = "symbol"
    sort_direction: str = "asc"
    limit: int = 250


class ScreenerService:
    def __init__(self, db: Session, provider: MarketDataProvider) -> None:
        self.db = db
        self.provider = provider

    def run(self, filters: ScreenerFilters, user_id: str | None = None) -> list[dict[str, object]]:
        instruments = self.db.execute(select(Instrument).order_by(Instrument.symbol.asc())).scalars().all()
        quotes = {quote.symbol: quote for quote in self.provider.get_quotes([item.symbol for item in instruments])}

        allowed_symbols: set[str] | None = None
        if filters.watchlist_id:
            stmt = (
                select(Instrument.symbol, WatchlistItem.tags)
                .join(WatchlistItem, WatchlistItem.instrument_id == Instrument.id)
                .where(WatchlistItem.watchlist_id == filters.watchlist_id)
            )
            if user_id:
                stmt = stmt.join(Watchlist, Watchlist.id == WatchlistItem.watchlist_id).where(
                    Watchlist.user_id == user_id
                )
            item_rows = self.db.execute(stmt).all()
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
            if filters.volume_min is not None and (quote.volume is None or quote.volume < filters.volume_min):
                continue
            if filters.volume_max is not None and (quote.volume is None or quote.volume > filters.volume_max):
                continue

            market_cap = float(instrument.market_cap) if instrument.market_cap is not None else None
            if filters.market_cap_min is not None and (market_cap is None or market_cap < filters.market_cap_min):
                continue
            if filters.market_cap_max is not None and (market_cap is None or market_cap > filters.market_cap_max):
                continue

            if filters.sector and instrument.sector != filters.sector:
                continue
            if filters.asset_type and instrument.asset_type != filters.asset_type:
                continue
            if filters.symbol_query:
                normalized_query = filters.symbol_query.lower().strip()
                if normalized_query not in instrument.symbol.lower() and normalized_query not in instrument.name.lower():
                    continue

            if allowed_symbols is not None and instrument.symbol not in allowed_symbols:
                continue

            results.append(
                {
                    "symbol": instrument.symbol,
                    "name": instrument.name,
                    "sector": instrument.sector,
                    "asset_type": instrument.asset_type,
                    "market_cap": market_cap,
                    "price": quote.price,
                    "change_percent": quote.change_percent,
                    "volume": quote.volume,
                }
            )

        sort_key = filters.sort_by
        reverse = filters.sort_direction.lower() == "desc"
        if sort_key in {"price", "change_percent", "market_cap", "volume", "name", "symbol"}:
            results.sort(
                key=lambda row: self._sort_value(row.get(sort_key)),
                reverse=reverse,
            )
        else:
            results.sort(key=lambda row: self._sort_value(row.get("symbol")), reverse=False)

        limit = max(1, min(filters.limit, 1000))
        return results[:limit]

    def list_saved_screens(self, user_id: str) -> list[dict[str, Any]]:
        rows = self.db.execute(
            select(SavedScreen)
            .where(SavedScreen.user_id == user_id)
            .order_by(SavedScreen.created_at.desc())
        ).scalars().all()
        return [self._serialize_saved_screen(item) for item in rows]

    def create_saved_screen(self, user_id: str, name: str, criteria: dict[str, Any]) -> dict[str, Any]:
        screen = SavedScreen(user_id=user_id, name=name, criteria=criteria)
        self.db.add(screen)
        self.db.commit()
        self.db.refresh(screen)
        return self._serialize_saved_screen(screen)

    def update_saved_screen(
        self,
        user_id: str,
        screen_id: str,
        *,
        name: str | None = None,
        criteria: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        screen = self.db.execute(
            select(SavedScreen).where(SavedScreen.id == screen_id, SavedScreen.user_id == user_id)
        ).scalar_one_or_none()
        if screen is None:
            raise ValueError("Saved screen not found")

        if name is not None:
            screen.name = name
        if criteria is not None:
            screen.criteria = criteria
        self.db.commit()
        self.db.refresh(screen)
        return self._serialize_saved_screen(screen)

    def delete_saved_screen(self, user_id: str, screen_id: str) -> None:
        screen = self.db.execute(
            select(SavedScreen).where(SavedScreen.id == screen_id, SavedScreen.user_id == user_id)
        ).scalar_one_or_none()
        if screen is None:
            raise ValueError("Saved screen not found")
        self.db.delete(screen)
        self.db.commit()

    def run_saved_screen(self, user_id: str, screen_id: str) -> dict[str, Any]:
        screen = self.db.execute(
            select(SavedScreen).where(SavedScreen.id == screen_id, SavedScreen.user_id == user_id)
        ).scalar_one_or_none()
        if screen is None:
            raise ValueError("Saved screen not found")
        filters = self.filters_from_criteria(screen.criteria)
        results = self.run(filters, user_id=user_id)
        return {"screen": self._serialize_saved_screen(screen), "results": results}

    def filters_from_criteria(self, criteria: dict[str, Any]) -> ScreenerFilters:
        return ScreenerFilters(
            price_min=self._to_float(criteria.get("price_min")),
            price_max=self._to_float(criteria.get("price_max")),
            market_cap_min=self._to_float(criteria.get("market_cap_min")),
            market_cap_max=self._to_float(criteria.get("market_cap_max")),
            change_percent_min=self._to_float(criteria.get("change_percent_min")),
            change_percent_max=self._to_float(criteria.get("change_percent_max")),
            volume_min=self._to_float(criteria.get("volume_min")),
            volume_max=self._to_float(criteria.get("volume_max")),
            sector=self._to_str(criteria.get("sector")),
            asset_type=self._to_str(criteria.get("asset_type")),
            symbol_query=self._to_str(criteria.get("symbol_query")),
            watchlist_id=self._to_str(criteria.get("watchlist_id")),
            tag=self._to_str(criteria.get("tag")),
            sort_by=self._to_str(criteria.get("sort_by")) or "symbol",
            sort_direction=self._to_str(criteria.get("sort_direction")) or "asc",
            limit=self._to_int(criteria.get("limit"), default=250),
        )

    def _serialize_saved_screen(self, screen: SavedScreen) -> dict[str, Any]:
        return {
            "id": screen.id,
            "name": screen.name,
            "criteria": screen.criteria,
            "created_at": screen.created_at,
            "updated_at": screen.updated_at,
        }

    def _sort_value(self, value: object | None) -> tuple[int, object]:
        if value is None:
            return (1, 0)
        if isinstance(value, str):
            return (0, value.lower())
        if isinstance(value, int | float):
            return (0, float(value))
        return (0, value)

    def _to_float(self, value: object | None) -> float | None:
        if value is None:
            return None
        if isinstance(value, int | float):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return None
        return None

    def _to_str(self, value: object | None) -> str | None:
        if isinstance(value, str) and value.strip():
            return value.strip()
        return None

    def _to_int(self, value: object | None, *, default: int) -> int:
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return default
        return default
