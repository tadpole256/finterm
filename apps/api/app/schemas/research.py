from datetime import datetime

from pydantic import BaseModel, Field


class ResearchNoteView(BaseModel):
    id: str
    symbol: str | None
    title: str
    content: str
    note_type: str
    theme: str | None
    sector: str | None
    event_ref: str | None
    created_at: datetime
    updated_at: datetime


class CreateResearchNoteRequest(BaseModel):
    symbol: str | None = Field(default=None, max_length=24)
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    note_type: str = Field(min_length=1, max_length=32)
    theme: str | None = Field(default=None, max_length=64)
    sector: str | None = Field(default=None, max_length=64)
    event_ref: str | None = Field(default=None, max_length=120)


class UpdateResearchNoteRequest(BaseModel):
    symbol: str | None = Field(default=None, max_length=24)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1)
    note_type: str | None = Field(default=None, min_length=1, max_length=32)
    theme: str | None = Field(default=None, max_length=64)
    sector: str | None = Field(default=None, max_length=64)
    event_ref: str | None = Field(default=None, max_length=120)


class ThesisView(BaseModel):
    id: str
    symbol: str | None
    title: str
    status: str
    summary: str
    created_at: datetime
    updated_at: datetime


class CreateThesisRequest(BaseModel):
    symbol: str | None = Field(default=None, max_length=24)
    title: str = Field(min_length=1, max_length=200)
    status: str = Field(default="active", min_length=1, max_length=32)
    summary: str = Field(min_length=1)


class UpdateThesisRequest(BaseModel):
    symbol: str | None = Field(default=None, max_length=24)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    status: str | None = Field(default=None, min_length=1, max_length=32)
    summary: str | None = Field(default=None, min_length=1)


class NoteSynthesisResponse(BaseModel):
    scope_symbol: str | None
    scope_theme: str | None
    generated_at: datetime
    source_model: str
    explanation: str
    note_count: int
    thesis_count: int
    synthesized_thesis: str
    open_questions: list[str]
    risks: list[str]
    next_watch: list[str]


class ResearchQaCitation(BaseModel):
    source_type: str
    source_id: str
    symbol: str | None
    title: str
    snippet: str
    score: float
    as_of: datetime
    url: str | None


class ResearchQaResponse(BaseModel):
    question: str
    symbol: str | None
    answered_at: datetime
    source_model: str
    answer: str
    citations: list[ResearchQaCitation]
    coverage_count: int
    total_candidates: int
