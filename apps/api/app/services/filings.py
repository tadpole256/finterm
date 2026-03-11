from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Filing, FilingSummary, Instrument
from app.services.filings_provider import FilingDocument, FilingsProvider


class FilingsService:
    def __init__(self, db: Session, provider: FilingsProvider) -> None:
        self.db = db
        self.provider = provider

    def sync_recent_filings(self, *, since: datetime | None = None, limit: int = 100) -> dict[str, Any]:
        as_of = datetime.now(UTC)
        effective_since = since or as_of - timedelta(days=30)
        fetched = self.provider.list_recent_filings(since=effective_since, limit=limit)

        inserted_count = 0
        updated_summary_count = 0

        for document in fetched:
            instrument = self.db.execute(
                select(Instrument).where(Instrument.symbol == document.symbol)
            ).scalar_one_or_none()
            if instrument is None:
                continue

            filing = self.db.execute(
                select(Filing).where(
                    Filing.instrument_id == instrument.id,
                    Filing.accession_no == document.accession_no,
                )
            ).scalar_one_or_none()

            if filing is None:
                filing = Filing(
                    instrument_id=instrument.id,
                    accession_no=document.accession_no,
                    form_type=document.form_type,
                    filed_at=document.filed_at,
                    period_end=document.period_end,
                    filing_url=document.filing_url,
                    raw_text=document.raw_text,
                    source_provider=document.source_provider,
                )
                self.db.add(filing)
                self.db.flush()
                inserted_count += 1
            else:
                filing.form_type = document.form_type
                filing.filed_at = document.filed_at
                filing.period_end = document.period_end
                filing.filing_url = document.filing_url
                filing.raw_text = document.raw_text

            summary_payload = self._build_summary_payload(instrument.symbol, filing, document)
            summary = self.db.execute(
                select(FilingSummary).where(FilingSummary.filing_id == filing.id)
            ).scalar_one_or_none()
            if summary is None:
                summary = FilingSummary(
                    filing_id=filing.id,
                    summary=summary_payload["summary"],
                    key_changes=summary_payload["key_changes"],
                    risks=summary_payload["risks"],
                    forward_looking=summary_payload["forward_looking"],
                    takeaway=summary_payload["takeaway"],
                    model_name="template-change-detect-v1",
                )
                self.db.add(summary)
                updated_summary_count += 1
            else:
                summary.summary = summary_payload["summary"]
                summary.key_changes = summary_payload["key_changes"]
                summary.risks = summary_payload["risks"]
                summary.forward_looking = summary_payload["forward_looking"]
                summary.takeaway = summary_payload["takeaway"]
                summary.model_name = "template-change-detect-v1"
                updated_summary_count += 1

        self.db.commit()
        return {
            "fetched_count": len(fetched),
            "inserted_count": inserted_count,
            "updated_summary_count": updated_summary_count,
            "as_of": as_of,
        }

    def list_filings(self, symbol: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        stmt = (
            select(Filing, Instrument.symbol, FilingSummary)
            .join(Instrument, Instrument.id == Filing.instrument_id)
            .join(FilingSummary, FilingSummary.filing_id == Filing.id, isouter=True)
            .order_by(Filing.filed_at.desc())
            .limit(limit)
        )
        if symbol:
            stmt = stmt.where(Instrument.symbol == symbol.upper())

        rows = self.db.execute(stmt).all()
        return [self._serialize_filing_row(filing, ticker, summary, include_raw_text=False) for filing, ticker, summary in rows]

    def get_filing_detail(self, filing_id: str) -> dict[str, Any] | None:
        row = self.db.execute(
            select(Filing, Instrument.symbol, FilingSummary)
            .join(Instrument, Instrument.id == Filing.instrument_id)
            .join(FilingSummary, FilingSummary.filing_id == Filing.id, isouter=True)
            .where(Filing.id == filing_id)
            .limit(1)
        ).first()
        if row is None:
            return None
        filing, ticker, summary = row
        return self._serialize_filing_row(filing, ticker, summary, include_raw_text=True)

    def _serialize_filing_row(
        self,
        filing: Filing,
        symbol: str,
        summary: FilingSummary | None,
        *,
        include_raw_text: bool,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": filing.id,
            "symbol": symbol,
            "accession_no": filing.accession_no,
            "form_type": filing.form_type,
            "filed_at": filing.filed_at,
            "period_end": filing.period_end,
            "filing_url": filing.filing_url,
            "source_provider": filing.source_provider,
            "summary": None
            if summary is None
            else {
                "summary": summary.summary,
                "key_changes": summary.key_changes,
                "risks": summary.risks,
                "forward_looking": summary.forward_looking,
                "takeaway": summary.takeaway,
                "model_name": summary.model_name,
            },
        }
        if include_raw_text:
            payload["raw_text"] = filing.raw_text
        return payload

    def _build_summary_payload(
        self,
        symbol: str,
        filing: Filing,
        document: FilingDocument,
    ) -> dict[str, Any]:
        text = (document.raw_text or "").strip()
        previous_filing = (
            self.db.execute(
                select(Filing)
                .where(
                    Filing.instrument_id == filing.instrument_id,
                    Filing.id != filing.id,
                    Filing.form_type == filing.form_type,
                )
                .order_by(Filing.filed_at.desc())
                .limit(1)
            )
            .scalars()
            .first()
        )

        key_changes: list[str] = []
        if previous_filing and previous_filing.raw_text and text:
            previous_sentences = self._normalized_sentences(previous_filing.raw_text)
            current_sentences = self._normalized_sentences(text)
            additions = [line for line in current_sentences if line not in previous_sentences][:3]
            removals = [line for line in previous_sentences if line not in current_sentences][:2]
            for sentence in additions:
                key_changes.append(f"Added: {sentence}")
            for sentence in removals:
                key_changes.append(f"Removed: {sentence}")

        if not key_changes and text:
            key_changes = [line for line in self._normalized_sentences(text)[:3]]

        risks = self._extract_matches(
            text,
            keywords=["risk", "headwind", "uncertainty", "decline", "constraint", "geopolitical"],
            fallback="No explicit risk language detected in parsed excerpt.",
        )
        forward_looking = self._extract_matches(
            text,
            keywords=["expect", "outlook", "guidance", "plan", "will", "forecast"],
            fallback="No explicit forward-looking language detected in parsed excerpt.",
        )

        summary = (
            f"{symbol} {document.form_type} filed {document.filed_at.date().isoformat()}: "
            + (self._normalized_sentences(text)[0] if text else "No filing text available.")
        )
        takeaway = (
            "Filing introduces material textual changes versus prior report."
            if previous_filing and key_changes
            else "Initial filing snapshot captured; monitor subsequent updates for meaningful deltas."
        )

        return {
            "summary": summary,
            "key_changes": key_changes[:5],
            "risks": risks[:4],
            "forward_looking": forward_looking[:4],
            "takeaway": takeaway,
        }

    def _normalized_sentences(self, text: str) -> list[str]:
        raw_chunks = text.replace("\n", " ").split(".")
        cleaned: list[str] = []
        for chunk in raw_chunks:
            sentence = " ".join(chunk.split()).strip()
            if not sentence:
                continue
            cleaned.append(sentence[:240])
        return cleaned

    def _extract_matches(self, text: str, *, keywords: list[str], fallback: str) -> list[str]:
        lines = self._normalized_sentences(text)
        matches = [
            line
            for line in lines
            if any(keyword in line.lower() for keyword in keywords)
        ]
        if matches:
            return matches
        if text:
            return [fallback]
        return ["No filing text available."]
