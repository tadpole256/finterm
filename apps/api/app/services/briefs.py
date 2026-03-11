from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import (
    Alert,
    DailyBrief,
    Filing,
    Notification,
    Portfolio,
    Position,
    Watchlist,
    WatchlistItem,
)
from app.services.market_provider import MarketDataProvider


class BriefService:
    def __init__(self, db: Session, provider: MarketDataProvider) -> None:
        self.db = db
        self.provider = provider

    def latest_brief(self, user_id: str) -> dict[str, Any] | None:
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
            return None
        return self._serialize_brief(brief)

    def generate_daily_brief(self, user_id: str, *, generated_at: datetime | None = None) -> dict[str, Any]:
        now = generated_at or datetime.now(UTC)
        market_snapshot = self.provider.list_market_snapshot()[:3]
        active_alert_count = self.db.execute(
            select(func.count(Alert.id)).where(Alert.user_id == user_id, Alert.status == "active")
        ).scalar_one()
        due_alert_count = self.db.execute(
            select(func.count(Alert.id)).where(
                Alert.user_id == user_id,
                Alert.status == "active",
                Alert.next_eval_at.is_not(None),
                Alert.next_eval_at <= now + timedelta(minutes=10),
            )
        ).scalar_one()
        watchlist_count = self.db.execute(
            select(func.count(Watchlist.id)).where(Watchlist.user_id == user_id)
        ).scalar_one()
        tracked_symbols_count = self.db.execute(
            select(func.count(WatchlistItem.id))
            .join(Watchlist, Watchlist.id == WatchlistItem.watchlist_id)
            .where(Watchlist.user_id == user_id)
        ).scalar_one()
        open_positions_count = self.db.execute(
            select(func.count(Position.id))
            .join(Portfolio, Portfolio.id == Position.portfolio_id)
            .where(Portfolio.user_id == user_id)
        ).scalar_one()

        start_of_day = datetime.combine(now.date(), datetime.min.time(), tzinfo=UTC)
        filings_last_day = self.db.execute(
            select(func.count(Filing.id)).where(Filing.filed_at >= start_of_day - timedelta(days=1))
        ).scalar_one()
        macro_events_today = [
            event for event in self.provider.get_macro_events() if event.scheduled_at.date() == now.date()
        ]

        headline = (
            f"{len(market_snapshot)} market anchors, {active_alert_count} active alerts, "
            f"{len(macro_events_today)} macro events today"
        )
        bullets = [
            *[
                f"{quote.symbol}: {quote.price:.2f} ({quote.change_percent:+.2f}%)"
                for quote in market_snapshot
            ],
            f"Watchlists: {watchlist_count} lists / {tracked_symbols_count} tracked symbols.",
            f"Portfolio: {open_positions_count} open positions. Due alerts in next cycle: {due_alert_count}.",
            f"Filings in last 24h across tracked universe: {filings_last_day}.",
        ]
        body = (
            "Template brief generated from local provider + workspace state. "
            "Use this as a triage view, not a predictive signal."
        )

        brief = DailyBrief(
            user_id=user_id,
            headline=headline,
            bullets=bullets,
            body=body,
            generated_at=now,
            source_model="template-phase5",
        )
        self.db.add(brief)
        self.db.flush()

        notification = Notification(
            user_id=user_id,
            daily_brief_id=brief.id,
            channel="in_app",
            title="Daily brief ready",
            body=headline,
            status="sent",
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(brief)

        return self._serialize_brief(brief)

    def generate_daily_brief_if_due(
        self, user_id: str, *, generated_at: datetime | None = None
    ) -> dict[str, Any] | None:
        now = generated_at or datetime.now(UTC)
        latest_brief = (
            self.db.execute(
                select(DailyBrief)
                .where(DailyBrief.user_id == user_id)
                .order_by(DailyBrief.generated_at.desc())
                .limit(1)
            )
            .scalars()
            .first()
        )
        if latest_brief and latest_brief.generated_at.date() == now.date():
            return None
        return self.generate_daily_brief(user_id=user_id, generated_at=now)

    def _serialize_brief(self, brief: DailyBrief) -> dict[str, Any]:
        return {
            "id": brief.id,
            "headline": brief.headline,
            "bullets": brief.bullets,
            "body": brief.body,
            "generated_at": brief.generated_at,
            "source_model": brief.source_model,
        }
