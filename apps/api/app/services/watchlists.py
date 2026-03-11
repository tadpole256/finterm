from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.db.models import Instrument, Watchlist, WatchlistItem
from app.services.market_provider import MarketDataProvider


class WatchlistService:
    def __init__(self, db: Session, provider: MarketDataProvider) -> None:
        self.db = db
        self.provider = provider

    def list_watchlists(self, user_id: str) -> list[dict[str, object]]:
        watchlists = (
            self.db.execute(
                select(Watchlist)
                .where(Watchlist.user_id == user_id)
                .options(joinedload(Watchlist.items).joinedload(WatchlistItem.instrument))
                .order_by(Watchlist.created_at.asc())
            )
            .scalars()
            .unique()
            .all()
        )
        return [self._serialize_watchlist(watchlist) for watchlist in watchlists]

    def create_watchlist(self, user_id: str, name: str, description: str | None) -> dict[str, object]:
        watchlist = Watchlist(user_id=user_id, name=name, description=description)
        self.db.add(watchlist)
        self.db.commit()
        self.db.refresh(watchlist)
        return self._serialize_watchlist(watchlist)

    def update_watchlist(
        self,
        user_id: str,
        watchlist_id: str,
        name: str | None,
        description: str | None,
    ) -> dict[str, object]:
        watchlist = self._owned_watchlist(user_id, watchlist_id)
        if name is not None:
            watchlist.name = name
        watchlist.description = description
        self.db.commit()
        self.db.refresh(watchlist)
        return self._serialize_watchlist(watchlist)

    def delete_watchlist(self, user_id: str, watchlist_id: str) -> None:
        watchlist = self._owned_watchlist(user_id, watchlist_id)
        self.db.delete(watchlist)
        self.db.commit()

    def add_item(self, user_id: str, watchlist_id: str, symbol: str, tags: list[str]) -> dict[str, object]:
        watchlist = self._owned_watchlist(user_id, watchlist_id)
        instrument = self.db.execute(
            select(Instrument).where(Instrument.symbol == symbol.upper())
        ).scalar_one_or_none()
        if instrument is None:
            raise ValueError(f"Unknown instrument symbol {symbol}")

        max_sort = self.db.execute(
            select(func.max(WatchlistItem.sort_order)).where(WatchlistItem.watchlist_id == watchlist.id)
        ).scalar_one()

        item = WatchlistItem(
            watchlist_id=watchlist.id,
            instrument_id=instrument.id,
            tags=tags,
            sort_order=(max_sort or 0) + 1,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(watchlist)
        return self._serialize_watchlist(
            self.db.execute(
                select(Watchlist)
                .where(Watchlist.id == watchlist.id)
                .options(joinedload(Watchlist.items).joinedload(WatchlistItem.instrument))
            )
            .scalars()
            .unique()
            .one()
        )

    def reorder_items(self, user_id: str, watchlist_id: str, item_ids: Sequence[str]) -> dict[str, object]:
        watchlist = self._owned_watchlist(user_id, watchlist_id)
        items = (
            self.db.execute(select(WatchlistItem).where(WatchlistItem.watchlist_id == watchlist.id))
            .scalars()
            .all()
        )
        item_map = {item.id: item for item in items}

        if set(item_ids) != set(item_map.keys()):
            raise ValueError("Reorder payload must include all item IDs exactly once")

        for index, item_id in enumerate(item_ids):
            item_map[item_id].sort_order = index

        self.db.commit()
        return self._serialize_watchlist(
            self.db.execute(
                select(Watchlist)
                .where(Watchlist.id == watchlist.id)
                .options(joinedload(Watchlist.items).joinedload(WatchlistItem.instrument))
            )
            .scalars()
            .unique()
            .one()
        )

    def remove_item(self, user_id: str, watchlist_id: str, item_id: str) -> None:
        watchlist = self._owned_watchlist(user_id, watchlist_id)
        item = self.db.execute(
            select(WatchlistItem).where(
                WatchlistItem.watchlist_id == watchlist.id,
                WatchlistItem.id == item_id,
            )
        ).scalar_one_or_none()
        if item is None:
            raise ValueError("Watchlist item not found")
        self.db.delete(item)
        self.db.commit()

    def _owned_watchlist(self, user_id: str, watchlist_id: str) -> Watchlist:
        watchlist = self.db.execute(
            select(Watchlist)
            .where(Watchlist.id == watchlist_id, Watchlist.user_id == user_id)
            .options(joinedload(Watchlist.items).joinedload(WatchlistItem.instrument))
        ).scalars().unique().one_or_none()

        if watchlist is None:
            raise ValueError("Watchlist not found")
        return watchlist

    def _serialize_watchlist(self, watchlist: Watchlist) -> dict[str, object]:
        ordered_items = sorted(watchlist.items, key=lambda item: item.sort_order)
        symbols = [item.instrument.symbol for item in ordered_items if item.instrument is not None]
        quote_map = {quote.symbol: quote for quote in self.provider.get_quotes(symbols)}

        serialized_items: list[dict[str, object]] = []
        for item in ordered_items:
            instrument = item.instrument
            if instrument is None:
                continue
            quote = quote_map.get(instrument.symbol)
            if quote is None:
                continue
            serialized_items.append(
                {
                    "id": item.id,
                    "symbol": instrument.symbol,
                    "instrument_name": instrument.name,
                    "tags": item.tags,
                    "sort_order": item.sort_order,
                    "quote": {
                        "symbol": quote.symbol,
                        "name": quote.name,
                        "price": quote.price,
                        "change": quote.change,
                        "change_percent": quote.change_percent,
                        "volume": quote.volume,
                    },
                }
            )

        return {
            "id": watchlist.id,
            "name": watchlist.name,
            "description": watchlist.description,
            "items": serialized_items,
        }
