from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ScreenerResultView(BaseModel):
    symbol: str
    name: str
    sector: str | None
    asset_type: str
    market_cap: float | None
    price: float
    change_percent: float
    volume: float | None


class ScreenerRunResponse(BaseModel):
    results: list[ScreenerResultView]


class SavedScreenView(BaseModel):
    id: str
    name: str
    criteria: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class CreateSavedScreenRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    criteria: dict[str, Any] = Field(default_factory=dict)


class UpdateSavedScreenRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    criteria: dict[str, Any] | None = None


class SavedScreenRunResponse(BaseModel):
    screen: SavedScreenView
    results: list[ScreenerResultView]
