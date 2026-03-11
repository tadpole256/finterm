from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Filing, FilingSummary, Instrument, ResearchNote
from app.services.retrieval_provider import RetrievalProvider

TOKEN_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z0-9_]+")
STOP_WORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "that",
    "this",
    "into",
    "what",
    "when",
    "where",
    "why",
    "how",
    "over",
    "under",
    "about",
    "after",
    "before",
    "have",
    "has",
    "had",
    "are",
    "was",
    "were",
    "will",
    "would",
    "could",
    "should",
    "their",
    "there",
    "than",
    "your",
    "ours",
    "them",
    "then",
    "which",
}


@dataclass(slots=True)
class CandidateDoc:
    source_type: str
    source_id: str
    symbol: str | None
    title: str
    text: str
    as_of: datetime
    url: str | None


@dataclass(slots=True)
class ScoreBreakdown:
    total: float
    lexical: float
    semantic: float
    recency: float
    snippet: str


def answer_research_question(
    db: Session,
    retrieval_provider: RetrievalProvider,
    user_id: str,
    question: str,
    symbol: str | None = None,
    limit: int = 6,
) -> dict[str, object]:
    normalized_question = question.strip()
    if not normalized_question:
        raise ValueError("question is required")

    scope_symbol = symbol.upper() if symbol else None
    candidates = _collect_candidates(db, user_id=user_id, symbol=scope_symbol)
    if not candidates:
        return {
            "question": normalized_question,
            "symbol": scope_symbol,
            "answered_at": datetime.now(UTC),
            "source_model": f"hybrid-{retrieval_provider.model_name()}",
            "answer": "No notes or filings found in the selected scope.",
            "citations": [],
            "coverage_count": 0,
            "total_candidates": 0,
        }

    question_tokens = _tokenize(normalized_question)
    semantic_scores = _semantic_scores(retrieval_provider, normalized_question, candidates)

    ranked: list[tuple[CandidateDoc, ScoreBreakdown]] = []
    for index, candidate in enumerate(candidates):
        score = _score_candidate(
            candidate=candidate,
            question_tokens=question_tokens,
            semantic_score=semantic_scores[index] if index < len(semantic_scores) else 0.0,
        )
        ranked.append((candidate, score))

    ranked.sort(key=lambda item: item[1].total, reverse=True)
    top_ranked = ranked[: max(1, min(limit, 10))]

    if top_ranked and top_ranked[0][1].total <= 0:
        # Fallback: if scoring is flat, keep newest docs first.
        top_ranked = sorted(
            top_ranked,
            key=lambda item: _normalize_datetime(item[0].as_of),
            reverse=True,
        )

    citations = []
    summary_lines: list[str] = []
    for candidate, breakdown in top_ranked:
        citations.append(
            {
                "source_type": candidate.source_type,
                "source_id": candidate.source_id,
                "symbol": candidate.symbol,
                "title": candidate.title,
                "snippet": breakdown.snippet,
                "score": round(breakdown.total, 4),
                "lexical_score": round(breakdown.lexical, 4),
                "semantic_score": round(breakdown.semantic, 4),
                "recency_score": round(breakdown.recency, 4),
                "as_of": candidate.as_of,
                "url": candidate.url,
            }
        )
        summary_lines.append(f"{candidate.title}: {breakdown.snippet}")

    answer = _build_answer(normalized_question, summary_lines)

    return {
        "question": normalized_question,
        "symbol": scope_symbol,
        "answered_at": datetime.now(UTC),
        "source_model": f"hybrid-{retrieval_provider.model_name()}",
        "answer": answer,
        "citations": citations,
        "coverage_count": len(citations),
        "total_candidates": len(candidates),
    }


def _collect_candidates(db: Session, user_id: str, symbol: str | None) -> list[CandidateDoc]:
    docs: list[CandidateDoc] = []

    notes_stmt = (
        select(ResearchNote, Instrument.symbol)
        .join(Instrument, Instrument.id == ResearchNote.instrument_id, isouter=True)
        .where(ResearchNote.user_id == user_id)
        .order_by(ResearchNote.updated_at.desc())
        .limit(250)
    )
    if symbol:
        notes_stmt = notes_stmt.where(Instrument.symbol == symbol)

    for note, note_symbol in db.execute(notes_stmt).all():
        docs.append(
            CandidateDoc(
                source_type="research_note",
                source_id=note.id,
                symbol=note_symbol,
                title=note.title,
                text=note.content,
                as_of=note.updated_at,
                url=None,
            )
        )

    filings_stmt = (
        select(Filing, FilingSummary, Instrument.symbol)
        .join(Instrument, Instrument.id == Filing.instrument_id)
        .join(FilingSummary, FilingSummary.filing_id == Filing.id, isouter=True)
        .order_by(Filing.filed_at.desc())
        .limit(150)
    )
    if symbol:
        filings_stmt = filings_stmt.where(Instrument.symbol == symbol)

    for filing, summary, filing_symbol in db.execute(filings_stmt).all():
        if summary is not None:
            summary_text = " ".join(
                [
                    summary.summary,
                    *summary.key_changes,
                    *summary.risks,
                    *summary.forward_looking,
                    summary.takeaway,
                ]
            )
        else:
            summary_text = filing.raw_text or ""

        docs.append(
            CandidateDoc(
                source_type="filing",
                source_id=filing.id,
                symbol=filing_symbol,
                title=f"{filing_symbol} {filing.form_type} ({filing.filed_at.date().isoformat()})",
                text=summary_text,
                as_of=filing.filed_at,
                url=filing.filing_url,
            )
        )

    return docs


def _semantic_scores(
    retrieval_provider: RetrievalProvider,
    question: str,
    candidates: list[CandidateDoc],
) -> list[float]:
    docs = [candidate.text for candidate in candidates]
    vectors = retrieval_provider.embed([question, *docs])
    if len(vectors) != len(docs) + 1:
        return [0.0 for _ in docs]

    query_vector = vectors[0]
    return [max(0.0, _cosine_similarity(query_vector, vector)) for vector in vectors[1:]]


def _score_candidate(
    candidate: CandidateDoc,
    question_tokens: set[str],
    semantic_score: float,
) -> ScoreBreakdown:
    text = candidate.text.strip()
    if not text:
        return ScoreBreakdown(total=0.0, lexical=0.0, semantic=0.0, recency=0.0, snippet="No text extracted.")

    doc_tokens = _tokenize(text)
    overlap = question_tokens & doc_tokens if question_tokens else set()

    lexical_score = 0.0
    if question_tokens:
        lexical_score = len(overlap) / max(len(question_tokens), 1)

    age_days = max((datetime.now(UTC) - _normalize_datetime(candidate.as_of)).days, 0)
    recency_score = max(0.0, 1 - (age_days / 365))

    snippet = _extract_snippet(text, overlap)
    total_score = (0.55 * semantic_score) + (0.35 * lexical_score) + (0.10 * recency_score)
    return ScoreBreakdown(
        total=total_score,
        lexical=lexical_score,
        semantic=semantic_score,
        recency=recency_score,
        snippet=snippet,
    )


def _extract_snippet(text: str, overlap_tokens: set[str]) -> str:
    compact = " ".join(text.split())
    if not compact:
        return "No detail available."

    sentences = re.split(r"(?<=[.!?])\s+", compact)
    if overlap_tokens:
        for sentence in sentences:
            sentence_tokens = _tokenize(sentence)
            if overlap_tokens & sentence_tokens:
                return _clip(sentence)
    return _clip(sentences[0] if sentences else compact)


def _build_answer(question: str, summary_lines: list[str]) -> str:
    if not summary_lines:
        return "No supporting notes or filings were found for this question."

    bullets = summary_lines[:4]
    narrative = " ".join(f"- {line}" for line in bullets)
    return (
        f"Question: {question}\n"
        "Highest-signal context from your notes and filings:\n"
        f"{narrative}\n"
        "Use citations below to verify source details."
    )


def _tokenize(text: str) -> set[str]:
    tokens = {
        token.lower()
        for token in TOKEN_PATTERN.findall(text)
        if len(token) > 2 and token.lower() not in STOP_WORDS
    }
    return tokens


def _cosine_similarity(vector_a: list[float], vector_b: list[float]) -> float:
    if len(vector_a) != len(vector_b):
        return 0.0
    dot_product = sum(left * right for left, right in zip(vector_a, vector_b, strict=False))
    norm_a = math.sqrt(sum(value * value for value in vector_a))
    norm_b = math.sqrt(sum(value * value for value in vector_b))
    if norm_a <= 0 or norm_b <= 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


def _clip(text: str, max_len: int = 220) -> str:
    if len(text) <= max_len:
        return text
    return f"{text[:max_len].rstrip()}..."


def _normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value
