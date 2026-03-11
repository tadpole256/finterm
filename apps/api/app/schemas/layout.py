from pydantic import BaseModel


class LayoutStateResponse(BaseModel):
    workspace: str
    state: dict[str, object]


class UpsertLayoutStateRequest(BaseModel):
    state: dict[str, object]
