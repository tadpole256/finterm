from __future__ import annotations

import logging
import os
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

API_APP_ROOT = Path(__file__).resolve().parents[2] / "api"
if str(API_APP_ROOT) not in sys.path:
    sys.path.insert(0, str(API_APP_ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


class WorkerApp:
    def __init__(self) -> None:
        from app.core.config import get_settings
        from app.db.session import SessionLocal
        from app.services.alerts import AlertsService
        from app.services.briefs import BriefService
        from app.services.filings import FilingsService
        from app.services.filings_provider import filings_provider_from_name
        from app.services.macro import MacroService
        from app.services.macro_provider import macro_provider_from_name
        from app.services.market_provider import provider_from_name

        settings = get_settings()
        self.session_local = SessionLocal
        self.alerts_service_cls: type[Any] = AlertsService
        self.brief_service_cls: type[Any] = BriefService
        self.filings_service_cls: type[Any] = FilingsService
        self.macro_service_cls: type[Any] = MacroService
        self.user_id = settings.user_seed_id
        self.provider = provider_from_name(settings.market_data_provider)
        self.filings_provider = filings_provider_from_name(settings.filings_provider)
        self.macro_provider = macro_provider_from_name(settings.macro_provider)
        self.poll_seconds = max(10, int(os.getenv("WORKER_POLL_SECONDS", "60")))
        self.filings_sync_minutes = max(15, int(os.getenv("WORKER_FILINGS_SYNC_MINUTES", "360")))
        self.macro_sync_minutes = max(15, int(os.getenv("WORKER_MACRO_SYNC_MINUTES", "60")))
        self.last_filings_sync_at: datetime | None = None
        self.last_macro_sync_at: datetime | None = None

    def run_tick(self) -> None:
        now = datetime.now(UTC)
        filings_summary: dict[str, Any] | None = None
        macro_summary: dict[str, Any] | None = None

        with self.session_local() as db:
            alert_summary = self.alerts_service_cls(db, self.provider).evaluate_due_alerts(
                user_id=self.user_id,
                now=now,
            )
            brief = self.brief_service_cls(db, self.provider).generate_daily_brief_if_due(
                user_id=self.user_id,
                generated_at=now,
            )

            if self._sync_due(self.last_filings_sync_at, now, self.filings_sync_minutes):
                filings_summary = self.filings_service_cls(db, self.filings_provider).sync_recent_filings(
                    since=now - timedelta(days=30),
                    limit=200,
                )
                self.last_filings_sync_at = now

            if self._sync_due(self.last_macro_sync_at, now, self.macro_sync_minutes):
                macro_summary = self.macro_service_cls(db, self.macro_provider).sync()
                self.last_macro_sync_at = now

        logging.info(
            (
                "worker tick at %s evaluated=%s triggered=%s notifications=%s "
                "brief_generated=%s filings_sync=%s macro_sync=%s"
            ),
            now.isoformat(),
            alert_summary["evaluated_count"],
            alert_summary["triggered_count"],
            alert_summary["notifications_created"],
            "yes" if brief else "no",
            (
                f"fetched:{filings_summary['fetched_count']} inserted:{filings_summary['inserted_count']}"
                if filings_summary
                else "no"
            ),
            (
                f"series:{macro_summary['series_upserted']} events:{macro_summary['events_inserted']}"
                if macro_summary
                else "no"
            ),
        )

    def run_forever(self) -> None:
        logging.info("worker started poll_seconds=%s", self.poll_seconds)
        while True:
            self.run_tick()
            time.sleep(self.poll_seconds)

    def _sync_due(self, last_sync: datetime | None, now: datetime, interval_minutes: int) -> bool:
        if last_sync is None:
            return True
        return now >= last_sync + timedelta(minutes=interval_minutes)


if __name__ == "__main__":
    WorkerApp().run_forever()
