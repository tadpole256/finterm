from __future__ import annotations

import logging
import os
import sys
import time
from datetime import UTC, datetime
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
        from app.services.market_provider import provider_from_name

        settings = get_settings()
        self.session_local = SessionLocal
        self.alerts_service_cls: type[Any] = AlertsService
        self.brief_service_cls: type[Any] = BriefService
        self.user_id = settings.user_seed_id
        self.provider = provider_from_name(settings.market_data_provider)
        self.poll_seconds = max(10, int(os.getenv("WORKER_POLL_SECONDS", "60")))

    def run_tick(self) -> None:
        now = datetime.now(UTC)
        with self.session_local() as db:
            alert_summary = self.alerts_service_cls(db, self.provider).evaluate_due_alerts(
                user_id=self.user_id,
                now=now,
            )
            brief = self.brief_service_cls(db, self.provider).generate_daily_brief_if_due(
                user_id=self.user_id,
                generated_at=now,
            )

        logging.info(
            "worker tick at %s evaluated=%s triggered=%s notifications=%s brief_generated=%s",
            now.isoformat(),
            alert_summary["evaluated_count"],
            alert_summary["triggered_count"],
            alert_summary["notifications_created"],
            "yes" if brief else "no",
        )

    def run_forever(self) -> None:
        logging.info("worker started poll_seconds=%s", self.poll_seconds)
        while True:
            self.run_tick()
            time.sleep(self.poll_seconds)


if __name__ == "__main__":
    WorkerApp().run_forever()
