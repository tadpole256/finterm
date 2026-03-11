from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import WorkspaceLayout


class LayoutService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_layout(self, user_id: str, workspace: str) -> dict[str, object]:
        layout = self.db.execute(
            select(WorkspaceLayout).where(
                WorkspaceLayout.user_id == user_id,
                WorkspaceLayout.workspace == workspace,
            )
        ).scalar_one_or_none()

        if layout is None:
            return {
                "workspace": workspace,
                "state": {
                    "sortBy": "symbol",
                    "sortDirection": "asc",
                    "filterTag": None,
                },
            }

        return {"workspace": workspace, "state": layout.state}

    def upsert_layout(self, user_id: str, workspace: str, state: dict[str, object]) -> dict[str, object]:
        layout = self.db.execute(
            select(WorkspaceLayout).where(
                WorkspaceLayout.user_id == user_id,
                WorkspaceLayout.workspace == workspace,
            )
        ).scalar_one_or_none()

        if layout is None:
            layout = WorkspaceLayout(user_id=user_id, workspace=workspace, state=state)
            self.db.add(layout)
        else:
            layout.state = state

        self.db.commit()
        return {"workspace": workspace, "state": layout.state}
