from pydantic import BaseModel, Field

from app.schemas.market import WatchlistView


class CreateWatchlistRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None


class UpdateWatchlistRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None


class AddWatchlistItemRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=24)
    tags: list[str] = Field(default_factory=list)


class ReorderWatchlistItemsRequest(BaseModel):
    item_ids: list[str]


class WatchlistResponse(WatchlistView):
    pass
