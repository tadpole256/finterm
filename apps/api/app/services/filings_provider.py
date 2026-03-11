from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol


@dataclass(slots=True)
class FilingDocument:
    symbol: str
    accession_no: str
    form_type: str
    filed_at: datetime
    period_end: datetime | None
    filing_url: str | None
    raw_text: str | None
    source_provider: str


class FilingsProvider(Protocol):
    def list_recent_filings(self, since: datetime | None = None, limit: int = 100) -> list[FilingDocument]: ...


class MockSecFilingsProvider(FilingsProvider):
    def __init__(self) -> None:
        fixture_dir = Path(__file__).resolve().parents[1] / "fixtures"
        self._rows: list[dict[str, object]] = json.loads((fixture_dir / "filings_feed.json").read_text())

    def list_recent_filings(self, since: datetime | None = None, limit: int = 100) -> list[FilingDocument]:
        documents: list[FilingDocument] = []
        for row in self._rows:
            filed_at = datetime.fromisoformat(str(row["filed_at"]).replace("Z", "+00:00"))
            period_end_raw = row.get("period_end")
            period_end = (
                datetime.fromisoformat(str(period_end_raw).replace("Z", "+00:00"))
                if period_end_raw
                else None
            )
            if since and filed_at < since:
                continue
            documents.append(
                FilingDocument(
                    symbol=str(row["symbol"]).upper(),
                    accession_no=str(row["accession_no"]),
                    form_type=str(row["form_type"]),
                    filed_at=filed_at,
                    period_end=period_end,
                    filing_url=str(row["filing_url"]) if row.get("filing_url") else None,
                    raw_text=str(row["raw_text"]) if row.get("raw_text") else None,
                    source_provider="mock_sec",
                )
            )
        documents.sort(key=lambda item: item.filed_at, reverse=True)
        return documents[:limit]


def filings_provider_from_name(name: str) -> FilingsProvider:
    normalized = name.lower().strip()
    if normalized in {"mock", "mock_sec", "sec"}:
        return MockSecFilingsProvider()
    raise ValueError(f"Unsupported filings provider '{name}'")
