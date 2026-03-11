from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    Alert,
    CatalystEvent,
    DailyBrief,
    Filing,
    FilingSummary,
    Instrument,
    MacroEvent,
    ResearchNote,
    Watchlist,
    WatchlistItem,
)
from app.services.cache import CacheService
from app.services.indicators import ema, macd, rsi, sma
from app.services.market_provider import MarketDataProvider
from app.services.watchlists import WatchlistService


class MarketWorkspaceService:
    def __init__(self, db: Session, provider: MarketDataProvider, cache: CacheService) -> None:
        self.db = db
        self.provider = provider
        self.cache = cache

    def dashboard(self, user_id: str) -> dict[str, Any]:
        meta = self.provider.provider_meta()
        cache_key = f"finterm:{meta.source_provider}:dashboard:{user_id}"

        cached = self.cache.get_json(cache_key)
        if cached.payload is not None:
            return cached.payload

        watchlists = WatchlistService(self.db, self.provider).list_watchlists(user_id)
        market_snapshot = [self._quote_dict(item) for item in self.provider.list_market_snapshot()]
        gainers, losers = self.provider.get_movers()

        now = datetime.now(UTC)
        macro_rows = (
            self.db.execute(
                select(MacroEvent)
                .where(MacroEvent.scheduled_at >= now - timedelta(days=1))
                .order_by(MacroEvent.scheduled_at.asc())
                .limit(12)
            )
            .scalars()
            .all()
        )
        macro_events = [
            {
                "id": row.id,
                "title": row.title,
                "scheduled_at": row.scheduled_at.isoformat(),
                "impact": row.impact,
                "actual": row.actual,
                "forecast": row.forecast,
            }
            for row in macro_rows
        ]
        if not macro_events:
            for event in self.provider.get_macro_events():
                macro_events.append(
                    {
                        "id": event.id,
                        "title": event.title,
                        "scheduled_at": event.scheduled_at.isoformat(),
                        "impact": event.impact,
                        "actual": event.actual,
                        "forecast": event.forecast,
                    }
                )

        alerts = self.db.execute(
            select(Alert).where(Alert.user_id == user_id, Alert.status == "active").limit(8)
        ).scalars()

        active_alerts = []
        for alert in alerts:
            symbol = "MARKET"
            if alert.instrument_id:
                instrument = self.db.execute(
                    select(Instrument).where(Instrument.id == alert.instrument_id)
                ).scalar_one_or_none()
                symbol = instrument.symbol if instrument is not None else "UNKNOWN"
            active_alerts.append(
                {
                    "id": alert.id,
                    "symbol": symbol,
                    "rule_summary": json.dumps(alert.rule),
                    "status": alert.status,
                    "triggered_at": alert.last_eval_at.isoformat() if alert.last_eval_at else None,
                }
            )

        brief = (
            self.db.execute(
                select(DailyBrief)
                .where(DailyBrief.user_id == user_id)
                .order_by(DailyBrief.generated_at.desc())
                .limit(1)
            )
            .scalars()
            .first()
        )
        if brief is None:
            brief_payload = {
                "id": "fallback-brief",
                "headline": "No brief generated yet",
                "bullets": ["Run seed data or daily brief worker to populate this panel."],
                "generated_at": datetime.now(UTC).isoformat(),
            }
        else:
            brief_payload = {
                "id": brief.id,
                "headline": brief.headline,
                "bullets": brief.bullets,
                "generated_at": brief.generated_at.isoformat(),
            }

        payload = {
            **self._meta_dict(meta, self.cache.backend != "redis"),
            "market_snapshot": market_snapshot,
            "watchlists": watchlists,
            "movers": {
                "gainers": [self._quote_dict(item) for item in gainers],
                "losers": [self._quote_dict(item) for item in losers],
            },
            "macro_events": macro_events,
            "active_alerts": active_alerts,
            "morning_brief": brief_payload,
        }

        self.cache.set_json(cache_key, jsonable_encoder(payload), ttl_seconds=30)
        return payload

    def instrument_search(self, query: str) -> list[dict[str, Any]]:
        return [
            {
                "symbol": instrument.symbol,
                "name": instrument.name,
                "exchange": instrument.exchange,
                "sector": instrument.sector,
                "industry": instrument.industry,
                "market_cap": instrument.market_cap,
            }
            for instrument in self.provider.search_instruments(query)
        ]

    def instrument_detail(self, symbol: str) -> dict[str, Any] | None:
        instrument = self.provider.get_instrument(symbol)
        if instrument is None:
            return None

        quote = self.provider.get_quotes([symbol])
        quote_payload = self._quote_dict(quote[0]) if quote else None
        return {
            "symbol": instrument.symbol,
            "name": instrument.name,
            "exchange": instrument.exchange,
            "sector": instrument.sector,
            "industry": instrument.industry,
            "market_cap": instrument.market_cap,
            "quote": quote_payload,
        }

    def quote_snapshots(self, symbols: list[str]) -> dict[str, Any]:
        meta = self.provider.provider_meta()
        quotes = [self._quote_dict(item) for item in self.provider.get_quotes(symbols)]
        return {
            **self._meta_dict(meta, self.cache.backend != "redis"),
            "quotes": quotes,
        }

    def bars(self, symbol: str, timeframe: str) -> dict[str, Any]:
        symbol = symbol.upper()
        meta = self.provider.provider_meta()
        cache_key = f"finterm:{meta.source_provider}:bars:{symbol}:{timeframe}"

        cached = self.cache.get_json(cache_key)
        if cached.payload is not None:
            return cached.payload

        bars = self.provider.get_historical_bars(symbol, timeframe, points=180)
        payload = {
            **self._meta_dict(meta, self.cache.backend != "redis"),
            "symbol": symbol,
            "timeframe": timeframe,
            "bars": [
                {
                    "ts": bar.ts.isoformat(),
                    "open": bar.open,
                    "high": bar.high,
                    "low": bar.low,
                    "close": bar.close,
                    "volume": bar.volume,
                }
                for bar in bars
            ],
        }

        self.cache.set_json(cache_key, jsonable_encoder(payload), ttl_seconds=120)
        return payload

    def security_workspace(
        self,
        symbol: str,
        user_id: str,
        timeframe: str = "6M",
    ) -> dict[str, Any] | None:
        symbol = symbol.upper()
        meta = self.provider.provider_meta()

        instrument = self.provider.get_instrument(symbol)
        if instrument is None:
            return None

        quote = self.provider.get_quotes([symbol])
        if not quote:
            return None

        bars = self.provider.get_historical_bars(symbol, timeframe=timeframe, points=180)
        filings = (
            self.db.execute(
                select(Filing, FilingSummary)
                .join(FilingSummary, FilingSummary.filing_id == Filing.id, isouter=True)
                .join(Instrument, Instrument.id == Filing.instrument_id)
                .where(Instrument.symbol == symbol)
                .order_by(Filing.filed_at.desc())
                .limit(5)
            )
            .all()
        )

        notes = (
            self.db.execute(
                select(ResearchNote)
                .join(Instrument, Instrument.id == ResearchNote.instrument_id)
                .where(ResearchNote.user_id == user_id, Instrument.symbol == symbol)
                .order_by(ResearchNote.updated_at.desc())
                .limit(5)
            )
            .scalars()
            .all()
        )

        catalysts = (
            self.db.execute(
                select(CatalystEvent)
                .join(Instrument, Instrument.id == CatalystEvent.instrument_id)
                .where(CatalystEvent.user_id == user_id, Instrument.symbol == symbol)
                .order_by(CatalystEvent.event_date.desc())
                .limit(5)
            )
            .scalars()
            .all()
        )

        watchlists = (
            self.db.execute(select(Watchlist).where(Watchlist.user_id == user_id).order_by(Watchlist.name.asc()))
            .scalars()
            .all()
        )

        item_rows = (
            self.db.execute(
                select(WatchlistItem.watchlist_id)
                .join(Instrument, Instrument.id == WatchlistItem.instrument_id)
                .where(Instrument.symbol == symbol)
            )
            .scalars()
            .all()
        )
        membership = set(item_rows)

        sma20_points = sma(bars, 20)
        sma50_points = sma(bars, 50)
        ema20_points = ema(bars, 20)
        rsi14_points = rsi(bars, 14)
        macd_points = macd(bars)

        what_changed = (
            "Mock delta: latest filing language emphasizes margin expansion and capex discipline. "
            "Track backlog conversion and guidance wording on next update."
        )

        payload = {
            **self._meta_dict(meta, self.cache.backend != "redis"),
            "instrument": {
                "symbol": instrument.symbol,
                "name": instrument.name,
                "exchange": instrument.exchange,
                "sector": instrument.sector,
                "industry": instrument.industry,
                "market_cap": instrument.market_cap,
                "description": None,
            },
            "quote": self._quote_dict(quote[0]),
            "bars": [
                {
                    "ts": bar.ts.isoformat(),
                    "open": bar.open,
                    "high": bar.high,
                    "low": bar.low,
                    "close": bar.close,
                    "volume": bar.volume,
                }
                for bar in bars
            ],
            "indicators": {
                "sma20": [
                    {"ts": point.ts.isoformat(), "value": point.value}
                    for point in sma20_points
                ],
                "sma50": [
                    {"ts": point.ts.isoformat(), "value": point.value}
                    for point in sma50_points
                ],
                "ema20": [
                    {"ts": point.ts.isoformat(), "value": point.value}
                    for point in ema20_points
                ],
                "rsi14": [
                    {"ts": point.ts.isoformat(), "value": point.value}
                    for point in rsi14_points
                ],
                "macd": [
                    {
                        "ts": point.ts.isoformat(),
                        "macd": point.macd,
                        "signal": point.signal,
                        "histogram": point.histogram,
                    }
                    for point in macd_points
                ],
            },
            "filings": [
                {
                    "id": filing.id,
                    "form_type": filing.form_type,
                    "filed_at": filing.filed_at.isoformat(),
                    "summary": summary.summary if summary else None,
                }
                for filing, summary in filings
            ],
            "notes": [
                {
                    "id": note.id,
                    "title": note.title,
                    "note_type": note.note_type,
                    "updated_at": note.updated_at.isoformat(),
                }
                for note in notes
            ],
            "catalysts": [
                {
                    "id": event.id,
                    "title": event.title,
                    "event_date": event.event_date.isoformat(),
                    "status": event.status,
                }
                for event in catalysts
            ],
            "what_changed": what_changed,
            "watchlists": [
                {"id": watchlist.id, "name": watchlist.name, "is_member": watchlist.id in membership}
                for watchlist in watchlists
            ],
        }
        return payload

    def _meta_dict(self, meta: Any, degraded: bool) -> dict[str, Any]:
        freshness_status = meta.freshness_status
        if degraded and freshness_status == "fresh":
            freshness_status = "degraded"
        return {
            "source_provider": meta.source_provider,
            "as_of": meta.as_of.isoformat(),
            "delay_seconds": meta.delay_seconds,
            "freshness_status": freshness_status,
            "is_stale": freshness_status != "fresh",
        }

    @staticmethod
    def _quote_dict(quote: Any) -> dict[str, Any]:
        return {
            "symbol": quote.symbol,
            "name": quote.name,
            "price": quote.price,
            "change": quote.change,
            "change_percent": quote.change_percent,
            "volume": quote.volume,
        }
