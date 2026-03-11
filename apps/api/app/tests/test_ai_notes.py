from datetime import UTC, datetime

from app.db.models import CatalystEvent, ResearchNote, Thesis
from app.services.ai_notes import synthesize_notes


def test_synthesize_notes_includes_questions_risks_and_watchlist() -> None:
    now = datetime.now(UTC)
    notes = [
        ResearchNote(
            id="1",
            user_id="u1",
            instrument_id=None,
            title="Thesis",
            content="Maintain conviction. What breaks the thesis?",
            note_type="thesis",
            theme="quality",
            sector=None,
            event_ref=None,
        ),
        ResearchNote(
            id="2",
            user_id="u1",
            instrument_id=None,
            title="Risk",
            content="Risk: margin compression if pricing power weakens.",
            note_type="risk",
            theme="quality",
            sector=None,
            event_ref=None,
        ),
    ]
    theses = [
        Thesis(
            id="t1",
            user_id="u1",
            instrument_id=None,
            title="Core",
            status="active",
            summary="Active thesis summary",
        )
    ]
    catalysts = [
        CatalystEvent(
            id="c1",
            user_id="u1",
            instrument_id=None,
            title="Earnings",
            event_date=now,
            status="scheduled",
            notes=None,
        )
    ]

    payload = synthesize_notes(notes=notes, theses=theses, catalysts=catalysts, symbol="AAPL", theme=None)

    assert payload["scope_symbol"] == "AAPL"
    assert payload["note_count"] == 2
    assert payload["thesis_count"] == 1
    assert payload["open_questions"]
    assert payload["risks"]
    assert payload["next_watch"]
