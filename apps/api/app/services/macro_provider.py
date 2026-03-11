from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol


@dataclass(slots=True)
class MacroSeriesRecord:
    code: str
    name: str
    description: str | None
    frequency: str
    country: str
    source_provider: str


@dataclass(slots=True)
class MacroCalendarRecord:
    series_code: str | None
    title: str
    scheduled_at: datetime
    impact: str
    actual: str | None
    forecast: str | None
    country: str
    source_provider: str


class MacroProvider(Protocol):
    def list_series(self) -> list[MacroSeriesRecord]: ...

    def list_events(self, since: datetime | None = None, limit: int = 200) -> list[MacroCalendarRecord]: ...


class MockMacroProvider(MacroProvider):
    def __init__(self) -> None:
        fixture_dir = Path(__file__).resolve().parents[1] / "fixtures"
        self._series_rows: list[dict[str, object]] = json.loads((fixture_dir / "macro_series.json").read_text())
        self._event_rows: list[dict[str, object]] = json.loads((fixture_dir / "macro_events.json").read_text())

    def list_series(self) -> list[MacroSeriesRecord]:
        return [
            MacroSeriesRecord(
                code=str(item["code"]),
                name=str(item["name"]),
                description=str(item["description"]) if item.get("description") else None,
                frequency=str(item.get("frequency", "monthly")),
                country=str(item.get("country", "US")),
                source_provider="mock_macro",
            )
            for item in self._series_rows
        ]

    def list_events(self, since: datetime | None = None, limit: int = 200) -> list[MacroCalendarRecord]:
        events: list[MacroCalendarRecord] = []
        for row in self._event_rows:
            scheduled_at = datetime.fromisoformat(str(row["scheduled_at"]).replace("Z", "+00:00"))
            if since and scheduled_at < since:
                continue
            events.append(
                MacroCalendarRecord(
                    series_code=str(row["series_code"]) if row.get("series_code") else None,
                    title=str(row["title"]),
                    scheduled_at=scheduled_at,
                    impact=str(row.get("impact", "medium")),
                    actual=str(row["actual"]) if row.get("actual") is not None else None,
                    forecast=str(row["forecast"]) if row.get("forecast") is not None else None,
                    country=str(row.get("country", "US")),
                    source_provider="mock_macro",
                )
            )
        events.sort(key=lambda item: item.scheduled_at)
        return events[:limit]


def macro_provider_from_name(name: str) -> MacroProvider:
    normalized = name.lower().strip()
    if normalized in {"mock", "mock_macro", "macro"}:
        return MockMacroProvider()
    raise ValueError(f"Unsupported macro provider '{name}'")
