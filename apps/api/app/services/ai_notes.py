from __future__ import annotations

import re
from datetime import UTC, datetime

from app.db.models import CatalystEvent, ResearchNote, Thesis

QUESTION_PATTERN = re.compile(r"[^.?!]*\?", re.MULTILINE)


def synthesize_notes(
    notes: list[ResearchNote],
    theses: list[Thesis],
    catalysts: list[CatalystEvent],
    symbol: str | None,
    theme: str | None,
) -> dict[str, object]:
    latest_thesis_note = next((note for note in notes if note.note_type == "thesis"), None)
    latest_active_thesis = next((thesis for thesis in theses if thesis.status == "active"), None)

    if latest_active_thesis is not None:
        thesis_text = latest_active_thesis.summary
    elif latest_thesis_note is not None:
        thesis_text = latest_thesis_note.content
    elif notes:
        thesis_text = notes[0].content
    else:
        thesis_text = "No notes in scope yet. Add thesis and risk notes to generate a stronger synthesis."

    open_questions = _extract_open_questions(notes)
    risks = _extract_risks(notes)
    next_watch = _extract_next_watch(catalysts, notes)

    if not open_questions:
        open_questions = [
            "What could invalidate the current thesis over the next two reporting cycles?",
            "Which leading indicators should trigger position-size adjustments?",
        ]

    if not risks:
        risks = ["No explicit risk notes found in scope."]

    if not next_watch:
        next_watch = ["No scheduled catalysts in scope."]

    return {
        "scope_symbol": symbol.upper() if symbol else None,
        "scope_theme": theme,
        "generated_at": datetime.now(UTC),
        "source_model": "heuristic-v1",
        "explanation": "Synthesized from user-authored notes and thesis records.",
        "note_count": len(notes),
        "thesis_count": len(theses),
        "synthesized_thesis": _clip_text(thesis_text),
        "open_questions": open_questions[:6],
        "risks": risks[:6],
        "next_watch": next_watch[:6],
    }


def _extract_open_questions(notes: list[ResearchNote]) -> list[str]:
    questions: list[str] = []
    watch_terms = ("watch", "monitor", "track", "confirm")

    for note in notes:
        matches = QUESTION_PATTERN.findall(note.content)
        questions.extend(_clean_lines(matches))

        for line in _split_lines(note.content):
            lower = line.lower()
            if any(term in lower for term in watch_terms) and "?" not in line:
                questions.append(f"{line.rstrip('.')}?")

    return _dedupe(questions)


def _extract_risks(notes: list[ResearchNote]) -> list[str]:
    results: list[str] = []
    risk_terms = ("risk", "downside", "headwind", "drawdown", "volatility")

    for note in notes:
        lines = _split_lines(note.content)
        if note.note_type == "risk":
            results.extend(lines)
            continue

        for line in lines:
            if any(term in line.lower() for term in risk_terms):
                results.append(line)

    return _dedupe(_clean_lines(results))


def _extract_next_watch(catalysts: list[CatalystEvent], notes: list[ResearchNote]) -> list[str]:
    results: list[str] = []

    for catalyst in catalysts:
        results.append(
            f"{catalyst.event_date.date().isoformat()} · {catalyst.title} ({catalyst.status})"
        )

    watch_terms = ("watch", "monitor", "track")
    for note in notes:
        for line in _split_lines(note.content):
            if any(term in line.lower() for term in watch_terms):
                results.append(line)

    return _dedupe(_clean_lines(results))


def _split_lines(text: str) -> list[str]:
    tokens = re.split(r"[\n.;]", text)
    return [token.strip() for token in tokens if token.strip()]


def _clean_lines(lines: list[str]) -> list[str]:
    return [line.strip().strip("-").strip() for line in lines if line.strip()]


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


def _clip_text(text: str, length: int = 420) -> str:
    if len(text) <= length:
        return text
    return f"{text[:length].rstrip()}..."
