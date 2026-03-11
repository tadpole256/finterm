from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.api.deps import get_user_id
from app.db.models import CatalystEvent, Instrument
from app.db.session import get_db
from app.schemas.research import (
    CreateResearchNoteRequest,
    CreateThesisRequest,
    NoteSynthesisResponse,
    ResearchNoteView,
    ResearchQaResponse,
    ThesisView,
    UpdateResearchNoteRequest,
    UpdateThesisRequest,
)
from app.services.ai_notes import synthesize_notes
from app.services.research import ResearchService
from app.services.research_qa import answer_research_question

router = APIRouter(prefix="/research", tags=["research"])
ai_router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/notes", response_model=list[ResearchNoteView])
def list_notes(
    q: str | None = Query(default=None),
    symbol: str | None = Query(default=None),
    note_type: str | None = Query(default=None),
    theme: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    return ResearchService(db).list_notes(
        user_id=user_id,
        query=q,
        symbol=symbol,
        note_type=note_type,
        theme=theme,
        limit=limit,
    )


@router.post("/notes", response_model=ResearchNoteView, status_code=status.HTTP_201_CREATED)
def create_note(
    payload: CreateResearchNoteRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        return ResearchService(db).create_note(user_id=user_id, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/notes/{note_id}", response_model=ResearchNoteView)
def update_note(
    note_id: str,
    payload: UpdateResearchNoteRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        return ResearchService(db).update_note(user_id=user_id, note_id=note_id, payload=payload)
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: str,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> Response:
    try:
        ResearchService(db).delete_note(user_id=user_id, note_id=note_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/theses", response_model=list[ThesisView])
def list_theses(
    symbol: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=200),
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    return ResearchService(db).list_theses(
        user_id=user_id,
        symbol=symbol,
        status=status_filter,
        limit=limit,
    )


@router.post("/theses", response_model=ThesisView, status_code=status.HTTP_201_CREATED)
def create_thesis(
    payload: CreateThesisRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        return ResearchService(db).create_thesis(user_id=user_id, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/theses/{thesis_id}", response_model=ThesisView)
def update_thesis(
    thesis_id: str,
    payload: UpdateThesisRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        return ResearchService(db).update_thesis(
            user_id=user_id,
            thesis_id=thesis_id,
            payload=payload,
        )
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.delete("/theses/{thesis_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_thesis(
    thesis_id: str,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> Response:
    try:
        ResearchService(db).delete_thesis(user_id=user_id, thesis_id=thesis_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/themes")
def list_themes(
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> dict[str, list[str]]:
    return {"themes": ResearchService(db).list_note_themes(user_id)}


@router.get("/synthesis", response_model=NoteSynthesisResponse)
def get_note_synthesis(
    symbol: str | None = Query(default=None),
    theme: str | None = Query(default=None),
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    if not symbol and not theme:
        raise HTTPException(status_code=400, detail="symbol or theme is required")

    service = ResearchService(db)
    notes = service.list_notes_for_synthesis(user_id=user_id, symbol=symbol, theme=theme)
    theses = service.list_theses_for_synthesis(user_id=user_id, symbol=symbol)

    catalyst_stmt = select(CatalystEvent).where(CatalystEvent.user_id == user_id)
    if symbol:
        catalyst_stmt = catalyst_stmt.join(
            Instrument,
            and_(
                Instrument.id == CatalystEvent.instrument_id,
                Instrument.symbol == symbol.upper(),
            ),
        )
    catalysts = list(
        db.execute(catalyst_stmt.order_by(CatalystEvent.event_date.asc()).limit(20)).scalars().all()
    )

    return synthesize_notes(notes=notes, theses=theses, catalysts=catalysts, symbol=symbol, theme=theme)


@ai_router.get("/note-synthesis", response_model=NoteSynthesisResponse)
def get_note_synthesis_alias(
    symbol: str | None = Query(default=None),
    theme: str | None = Query(default=None),
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    return get_note_synthesis(symbol=symbol, theme=theme, user_id=user_id, db=db)


@ai_router.get("/research-qa", response_model=ResearchQaResponse)
def get_research_qa(
    question: str = Query(min_length=3, max_length=1200),
    symbol: str | None = Query(default=None),
    limit: int = Query(default=6, ge=1, le=10),
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        return answer_research_question(
            db=db,
            user_id=user_id,
            question=question,
            symbol=symbol,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
