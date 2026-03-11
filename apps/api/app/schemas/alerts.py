from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AlertView(BaseModel):
    id: str
    symbol: str | None
    alert_type: str
    rule: dict[str, Any]
    status: str
    next_eval_at: datetime | None
    last_eval_at: datetime | None
    created_at: datetime
    updated_at: datetime


class CreateAlertRequest(BaseModel):
    symbol: str | None = Field(default=None, min_length=1, max_length=24)
    alert_type: str = Field(min_length=1, max_length=32)
    rule: dict[str, Any] = Field(default_factory=dict)
    status: str = Field(default="active", min_length=1, max_length=16)
    next_eval_at: datetime | None = None


class UpdateAlertRequest(BaseModel):
    symbol: str | None = Field(default=None, max_length=24)
    alert_type: str | None = Field(default=None, min_length=1, max_length=32)
    rule: dict[str, Any] | None = None
    status: str | None = Field(default=None, min_length=1, max_length=16)
    next_eval_at: datetime | None = None


class AlertEventView(BaseModel):
    id: str
    alert_id: str
    symbol: str | None
    triggered_at: datetime
    explanation: str | None
    severity: str
    payload: dict[str, Any]


class NotificationView(BaseModel):
    id: str
    title: str
    body: str
    status: str
    channel: str
    read_at: datetime | None
    created_at: datetime
    alert_event_id: str | None
    daily_brief_id: str | None


class MarkNotificationReadResponse(BaseModel):
    id: str
    status: str
    read_at: datetime | None


class AlertEvaluationResponse(BaseModel):
    evaluated_count: int
    triggered_count: int
    notifications_created: int
    evaluated_at: datetime


class DailyBriefView(BaseModel):
    id: str
    headline: str
    bullets: list[str]
    body: str | None
    generated_at: datetime
    source_model: str
