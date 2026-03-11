from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_provider, get_user_id
from app.db.session import get_db
from app.schemas.alerts import (
    AlertEvaluationResponse,
    AlertEventView,
    AlertView,
    CreateAlertRequest,
    DailyBriefView,
    MarkNotificationReadResponse,
    NotificationView,
    UpdateAlertRequest,
)
from app.services.alerts import AlertsService
from app.services.briefs import BriefService
from app.services.market_provider import MarketDataProvider

router = APIRouter(prefix="", tags=["alerts"])


@router.get("/alerts", response_model=list[AlertView])
def list_alerts(
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=200, ge=1, le=500),
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_provider),
) -> list[dict[str, object]]:
    return AlertsService(db, provider).list_alerts(user_id=user_id, status=status_filter, limit=limit)


@router.post("/alerts", response_model=AlertView, status_code=status.HTTP_201_CREATED)
def create_alert(
    payload: CreateAlertRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_provider),
) -> dict[str, object]:
    try:
        return AlertsService(db, provider).create_alert(user_id=user_id, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/alerts/{alert_id}", response_model=AlertView)
def update_alert(
    alert_id: str,
    payload: UpdateAlertRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_provider),
) -> dict[str, object]:
    try:
        return AlertsService(db, provider).update_alert(user_id=user_id, alert_id=alert_id, payload=payload)
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.delete("/alerts/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert(
    alert_id: str,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_provider),
) -> Response:
    try:
        AlertsService(db, provider).delete_alert(user_id=user_id, alert_id=alert_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/alerts/events", response_model=list[AlertEventView])
def list_alert_events(
    limit: int = Query(default=200, ge=1, le=500),
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_provider),
) -> list[dict[str, object]]:
    return AlertsService(db, provider).list_events(user_id=user_id, limit=limit)


@router.post("/alerts/evaluate", response_model=AlertEvaluationResponse)
def evaluate_alerts(
    limit: int = Query(default=200, ge=1, le=500),
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_provider),
) -> dict[str, object]:
    return AlertsService(db, provider).evaluate_due_alerts(user_id=user_id, limit=limit)


@router.get("/notifications", response_model=list[NotificationView])
def list_notifications(
    status_filter: str = Query(default="all", alias="status"),
    limit: int = Query(default=200, ge=1, le=500),
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_provider),
) -> list[dict[str, object]]:
    return AlertsService(db, provider).list_notifications(
        user_id=user_id,
        status=status_filter,
        limit=limit,
    )


@router.patch("/notifications/{notification_id}/read", response_model=MarkNotificationReadResponse)
def mark_notification_read(
    notification_id: str,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_provider),
) -> dict[str, object]:
    try:
        return AlertsService(db, provider).mark_notification_read(
            user_id=user_id,
            notification_id=notification_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/briefs/latest", response_model=DailyBriefView)
def latest_brief(
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_provider),
) -> dict[str, object]:
    brief = BriefService(db, provider).latest_brief(user_id=user_id)
    if brief is None:
        raise HTTPException(status_code=404, detail="No brief available")
    return brief


@router.post("/briefs/generate", response_model=DailyBriefView, status_code=status.HTTP_201_CREATED)
def generate_brief(
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_provider),
) -> dict[str, object]:
    return BriefService(db, provider).generate_daily_brief(user_id=user_id)
