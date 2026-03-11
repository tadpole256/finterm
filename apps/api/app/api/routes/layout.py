from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_user_id
from app.db.session import get_db
from app.schemas.layout import LayoutStateResponse, UpsertLayoutStateRequest
from app.services.layout import LayoutService

router = APIRouter(prefix="/workspaces/layout", tags=["workspace"])


@router.get("/{workspace}", response_model=LayoutStateResponse)
def get_layout(
    workspace: str,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    return LayoutService(db).get_layout(user_id, workspace)


@router.put("/{workspace}", response_model=LayoutStateResponse)
def upsert_layout(
    workspace: str,
    payload: UpsertLayoutStateRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
    user_id_query: str | None = Query(default=None, alias="user_id"),
) -> dict[str, object]:
    target_user = user_id_query or user_id
    return LayoutService(db).upsert_layout(target_user, workspace, payload.state)
