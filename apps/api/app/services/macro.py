from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import MacroEvent, MacroSeries
from app.services.macro_provider import MacroProvider


class MacroService:
    def __init__(self, db: Session, provider: MacroProvider) -> None:
        self.db = db
        self.provider = provider

    def sync(self) -> dict[str, Any]:
        as_of = datetime.now(UTC)
        series_records = self.provider.list_series()
        events = self.provider.list_events(since=as_of - timedelta(days=30), limit=400)

        series_by_code: dict[str, MacroSeries] = {}
        series_upserted = 0
        for record in series_records:
            row = self.db.execute(select(MacroSeries).where(MacroSeries.code == record.code)).scalar_one_or_none()
            if row is None:
                row = MacroSeries(
                    code=record.code,
                    name=record.name,
                    description=record.description,
                    frequency=record.frequency,
                    source_provider=record.source_provider,
                )
                self.db.add(row)
                self.db.flush()
            else:
                row.name = record.name
                row.description = record.description
                row.frequency = record.frequency
                row.source_provider = record.source_provider
            series_by_code[record.code] = row
            series_upserted += 1

        events_inserted = 0
        for event in events:
            series_id = series_by_code[event.series_code].id if event.series_code and event.series_code in series_by_code else None
            existing = self.db.execute(
                select(MacroEvent).where(
                    MacroEvent.title == event.title,
                    MacroEvent.scheduled_at == event.scheduled_at,
                    MacroEvent.country == event.country,
                )
            ).scalar_one_or_none()
            if existing:
                existing.series_id = series_id
                existing.actual = event.actual
                existing.forecast = event.forecast
                existing.impact = event.impact
                continue

            self.db.add(
                MacroEvent(
                    series_id=series_id,
                    title=event.title,
                    scheduled_at=event.scheduled_at,
                    actual=event.actual,
                    forecast=event.forecast,
                    impact=event.impact,
                    country=event.country,
                )
            )
            events_inserted += 1

        self.db.commit()
        return {
            "series_upserted": series_upserted,
            "events_inserted": events_inserted,
            "as_of": as_of,
        }

    def list_series(self, limit: int = 100) -> list[dict[str, Any]]:
        rows = self.db.execute(
            select(MacroSeries).order_by(MacroSeries.code.asc()).limit(limit)
        ).scalars().all()
        now = datetime.now(UTC)

        payload: list[dict[str, Any]] = []
        for row in rows:
            upcoming_count = self.db.execute(
                select(func.count(MacroEvent.id)).where(
                    MacroEvent.series_id == row.id,
                    MacroEvent.scheduled_at >= now,
                )
            ).scalar_one()
            next_event_at = self.db.execute(
                select(MacroEvent.scheduled_at)
                .where(
                    MacroEvent.series_id == row.id,
                    MacroEvent.scheduled_at >= now,
                )
                .order_by(MacroEvent.scheduled_at.asc())
                .limit(1)
            ).scalar_one_or_none()
            payload.append(
                {
                    "id": row.id,
                    "code": row.code,
                    "name": row.name,
                    "description": row.description,
                    "frequency": row.frequency,
                    "source_provider": row.source_provider,
                    "upcoming_event_count": int(upcoming_count),
                    "next_event_at": next_event_at,
                }
            )
        return payload

    def list_events(
        self,
        *,
        days_ahead: int = 14,
        country: str | None = None,
        impact: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        now = datetime.now(UTC)
        cutoff = now + timedelta(days=days_ahead)

        future_stmt = (
            select(MacroEvent, MacroSeries.code)
            .join(MacroSeries, MacroSeries.id == MacroEvent.series_id, isouter=True)
            .where(MacroEvent.scheduled_at >= now, MacroEvent.scheduled_at <= cutoff)
            .order_by(MacroEvent.scheduled_at.asc())
            .limit(limit)
        )
        if country:
            future_stmt = future_stmt.where(MacroEvent.country == country.upper())
        if impact:
            future_stmt = future_stmt.where(MacroEvent.impact == impact.lower())

        rows = self.db.execute(future_stmt).all()

        if not rows:
            fallback_stmt = (
                select(MacroEvent, MacroSeries.code)
                .join(MacroSeries, MacroSeries.id == MacroEvent.series_id, isouter=True)
                .order_by(MacroEvent.scheduled_at.desc())
                .limit(limit)
            )
            if country:
                fallback_stmt = fallback_stmt.where(MacroEvent.country == country.upper())
            if impact:
                fallback_stmt = fallback_stmt.where(MacroEvent.impact == impact.lower())
            rows = self.db.execute(fallback_stmt).all()
        return [
            {
                "id": event.id,
                "series_code": series_code,
                "title": event.title,
                "scheduled_at": event.scheduled_at,
                "impact": event.impact,
                "actual": event.actual,
                "forecast": event.forecast,
                "country": event.country,
            }
            for event, series_code in rows
        ]
