from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db.models import Instrument, ResearchNote, Thesis
from app.schemas.research import (
    CreateResearchNoteRequest,
    CreateThesisRequest,
    UpdateResearchNoteRequest,
    UpdateThesisRequest,
)


class ResearchService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_notes(
        self,
        user_id: str,
        query: str | None = None,
        symbol: str | None = None,
        note_type: str | None = None,
        theme: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, object]]:
        stmt = (
            select(ResearchNote, Instrument.symbol)
            .join(Instrument, Instrument.id == ResearchNote.instrument_id, isouter=True)
            .where(ResearchNote.user_id == user_id)
            .order_by(ResearchNote.updated_at.desc())
        )

        if query:
            normalized = f"%{query.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(ResearchNote.title).like(normalized),
                    func.lower(ResearchNote.content).like(normalized),
                    func.lower(func.coalesce(ResearchNote.theme, "")).like(normalized),
                )
            )

        if symbol:
            stmt = stmt.where(Instrument.symbol == symbol.upper())

        if note_type:
            stmt = stmt.where(ResearchNote.note_type == note_type)

        if theme:
            stmt = stmt.where(func.lower(func.coalesce(ResearchNote.theme, "")) == theme.lower())

        rows = self.db.execute(stmt.limit(max(1, min(limit, 200)))).all()
        return [self._serialize_note(note, symbol_value) for note, symbol_value in rows]

    def create_note(
        self,
        user_id: str,
        payload: CreateResearchNoteRequest,
    ) -> dict[str, object]:
        instrument_id = self._resolve_instrument_id(payload.symbol)
        note = ResearchNote(
            user_id=user_id,
            instrument_id=instrument_id,
            title=payload.title,
            content=payload.content,
            note_type=payload.note_type,
            theme=payload.theme,
            sector=payload.sector,
            event_ref=payload.event_ref,
        )
        self.db.add(note)
        self.db.commit()
        self.db.refresh(note)
        symbol = self._symbol_for_instrument_id(note.instrument_id)
        return self._serialize_note(note, symbol)

    def update_note(
        self,
        user_id: str,
        note_id: str,
        payload: UpdateResearchNoteRequest,
    ) -> dict[str, object]:
        note = self._owned_note(user_id, note_id)

        if "symbol" in payload.model_fields_set:
            note.instrument_id = self._resolve_instrument_id(payload.symbol)
        if payload.title is not None:
            note.title = payload.title
        if payload.content is not None:
            note.content = payload.content
        if payload.note_type is not None:
            note.note_type = payload.note_type
        if payload.theme is not None:
            note.theme = payload.theme
        if payload.sector is not None:
            note.sector = payload.sector
        if payload.event_ref is not None:
            note.event_ref = payload.event_ref

        self.db.commit()
        self.db.refresh(note)
        symbol = self._symbol_for_instrument_id(note.instrument_id)
        return self._serialize_note(note, symbol)

    def delete_note(self, user_id: str, note_id: str) -> None:
        note = self._owned_note(user_id, note_id)
        self.db.delete(note)
        self.db.commit()

    def list_theses(
        self,
        user_id: str,
        symbol: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, object]]:
        stmt = (
            select(Thesis, Instrument.symbol)
            .join(Instrument, Instrument.id == Thesis.instrument_id, isouter=True)
            .where(Thesis.user_id == user_id)
            .order_by(Thesis.updated_at.desc())
        )

        if symbol:
            stmt = stmt.where(Instrument.symbol == symbol.upper())
        if status:
            stmt = stmt.where(Thesis.status == status)

        rows = self.db.execute(stmt.limit(max(1, min(limit, 200)))).all()
        return [self._serialize_thesis(thesis, symbol_value) for thesis, symbol_value in rows]

    def create_thesis(self, user_id: str, payload: CreateThesisRequest) -> dict[str, object]:
        thesis = Thesis(
            user_id=user_id,
            instrument_id=self._resolve_instrument_id(payload.symbol),
            title=payload.title,
            status=payload.status,
            summary=payload.summary,
        )
        self.db.add(thesis)
        self.db.commit()
        self.db.refresh(thesis)
        symbol = self._symbol_for_instrument_id(thesis.instrument_id)
        return self._serialize_thesis(thesis, symbol)

    def update_thesis(
        self,
        user_id: str,
        thesis_id: str,
        payload: UpdateThesisRequest,
    ) -> dict[str, object]:
        thesis = self._owned_thesis(user_id, thesis_id)

        if "symbol" in payload.model_fields_set:
            thesis.instrument_id = self._resolve_instrument_id(payload.symbol)
        if payload.title is not None:
            thesis.title = payload.title
        if payload.status is not None:
            thesis.status = payload.status
        if payload.summary is not None:
            thesis.summary = payload.summary

        self.db.commit()
        self.db.refresh(thesis)
        symbol = self._symbol_for_instrument_id(thesis.instrument_id)
        return self._serialize_thesis(thesis, symbol)

    def delete_thesis(self, user_id: str, thesis_id: str) -> None:
        thesis = self._owned_thesis(user_id, thesis_id)
        self.db.delete(thesis)
        self.db.commit()

    def list_notes_for_synthesis(
        self,
        user_id: str,
        symbol: str | None,
        theme: str | None,
    ) -> list[ResearchNote]:
        stmt = (
            select(ResearchNote)
            .join(Instrument, Instrument.id == ResearchNote.instrument_id, isouter=True)
            .where(ResearchNote.user_id == user_id)
            .order_by(ResearchNote.updated_at.desc())
        )

        if symbol:
            stmt = stmt.where(Instrument.symbol == symbol.upper())
        if theme:
            stmt = stmt.where(func.lower(func.coalesce(ResearchNote.theme, "")) == theme.lower())

        return list(self.db.execute(stmt.limit(200)).scalars().all())

    def list_theses_for_synthesis(
        self,
        user_id: str,
        symbol: str | None,
    ) -> list[Thesis]:
        stmt = (
            select(Thesis)
            .join(Instrument, Instrument.id == Thesis.instrument_id, isouter=True)
            .where(Thesis.user_id == user_id)
            .order_by(Thesis.updated_at.desc())
        )

        if symbol:
            stmt = stmt.where(Instrument.symbol == symbol.upper())

        return list(self.db.execute(stmt.limit(50)).scalars().all())

    def list_note_themes(self, user_id: str) -> list[str]:
        stmt = (
            select(func.distinct(ResearchNote.theme))
            .where(ResearchNote.user_id == user_id, ResearchNote.theme.is_not(None))
            .order_by(ResearchNote.theme.asc())
        )
        values = self.db.execute(stmt).scalars().all()
        return [value for value in values if value]

    def _owned_note(self, user_id: str, note_id: str) -> ResearchNote:
        note = self.db.execute(
            select(ResearchNote).where(ResearchNote.id == note_id, ResearchNote.user_id == user_id)
        ).scalar_one_or_none()
        if note is None:
            raise ValueError("Research note not found")
        return note

    def _owned_thesis(self, user_id: str, thesis_id: str) -> Thesis:
        thesis = self.db.execute(
            select(Thesis).where(Thesis.id == thesis_id, Thesis.user_id == user_id)
        ).scalar_one_or_none()
        if thesis is None:
            raise ValueError("Thesis not found")
        return thesis

    def _resolve_instrument_id(self, symbol: str | None) -> str | None:
        if not symbol:
            return None
        instrument = self.db.execute(
            select(Instrument).where(Instrument.symbol == symbol.upper())
        ).scalar_one_or_none()
        if instrument is None:
            raise ValueError(f"Unknown instrument symbol {symbol}")
        return instrument.id

    def _symbol_for_instrument_id(self, instrument_id: str | None) -> str | None:
        if instrument_id is None:
            return None
        return self.db.execute(
            select(Instrument.symbol).where(Instrument.id == instrument_id)
        ).scalar_one_or_none()

    @staticmethod
    def _serialize_note(note: ResearchNote, symbol: str | None) -> dict[str, object]:
        return {
            "id": note.id,
            "symbol": symbol,
            "title": note.title,
            "content": note.content,
            "note_type": note.note_type,
            "theme": note.theme,
            "sector": note.sector,
            "event_ref": note.event_ref,
            "created_at": note.created_at,
            "updated_at": note.updated_at,
        }

    @staticmethod
    def _serialize_thesis(thesis: Thesis, symbol: str | None) -> dict[str, object]:
        return {
            "id": thesis.id,
            "symbol": symbol,
            "title": thesis.title,
            "status": thesis.status,
            "summary": thesis.summary,
            "created_at": thesis.created_at,
            "updated_at": thesis.updated_at,
        }
