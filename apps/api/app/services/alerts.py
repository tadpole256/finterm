from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from app.db.models import Alert, AlertEvent, Instrument, Notification
from app.schemas.alerts import CreateAlertRequest, UpdateAlertRequest
from app.services.market_provider import MarketDataProvider, Quote


@dataclass(slots=True)
class RuleEvaluation:
    triggered: bool
    explanation: str
    severity: str
    payload: dict[str, Any]


class AlertsService:
    def __init__(self, db: Session, provider: MarketDataProvider) -> None:
        self.db = db
        self.provider = provider

    def list_alerts(self, user_id: str, status: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
        stmt = (
            select(Alert, Instrument.symbol)
            .join(Instrument, Instrument.id == Alert.instrument_id, isouter=True)
            .where(Alert.user_id == user_id)
            .order_by(Alert.created_at.desc())
            .limit(limit)
        )
        if status and status != "all":
            stmt = stmt.where(Alert.status == status)

        rows = self.db.execute(stmt).all()
        return [self._serialize_alert(alert, symbol) for alert, symbol in rows]

    def create_alert(self, user_id: str, payload: CreateAlertRequest) -> dict[str, Any]:
        instrument_id: str | None = None
        symbol: str | None = None
        if payload.symbol:
            symbol = payload.symbol.upper()
            instrument = self.db.execute(
                select(Instrument).where(Instrument.symbol == symbol)
            ).scalar_one_or_none()
            if instrument is None:
                raise ValueError(f"Unknown instrument symbol {payload.symbol}")
            instrument_id = instrument.id

        now = datetime.now(UTC)
        meta = self.provider.provider_meta()
        alert = Alert(
            user_id=user_id,
            instrument_id=instrument_id,
            alert_type=payload.alert_type,
            rule=payload.rule,
            status=payload.status,
            next_eval_at=payload.next_eval_at or now,
            source_provider=meta.source_provider,
        )
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return self._serialize_alert(alert, symbol)

    def update_alert(self, user_id: str, alert_id: str, payload: UpdateAlertRequest) -> dict[str, Any]:
        alert = self.db.execute(
            select(Alert).where(Alert.id == alert_id, Alert.user_id == user_id)
        ).scalar_one_or_none()
        if alert is None:
            raise ValueError("Alert not found")

        updates = payload.model_dump(exclude_unset=True)
        symbol: str | None = None
        if "symbol" in updates:
            incoming_symbol = updates["symbol"]
            if incoming_symbol is None:
                alert.instrument_id = None
            elif isinstance(incoming_symbol, str):
                normalized = incoming_symbol.upper()
                instrument = self.db.execute(
                    select(Instrument).where(Instrument.symbol == normalized)
                ).scalar_one_or_none()
                if instrument is None:
                    raise ValueError(f"Unknown instrument symbol {incoming_symbol}")
                alert.instrument_id = instrument.id
                symbol = normalized
            else:
                raise ValueError("Invalid symbol value")

        if "alert_type" in updates and isinstance(updates["alert_type"], str):
            alert.alert_type = updates["alert_type"]
        if "rule" in updates and isinstance(updates["rule"], dict):
            alert.rule = updates["rule"]
        if "status" in updates and isinstance(updates["status"], str):
            alert.status = updates["status"]
        if "next_eval_at" in updates:
            next_eval_at = updates["next_eval_at"]
            if isinstance(next_eval_at, datetime) or next_eval_at is None:
                alert.next_eval_at = next_eval_at
            else:
                raise ValueError("Invalid next_eval_at value")

        self.db.commit()
        self.db.refresh(alert)
        if symbol is None and alert.instrument_id:
            instrument = self.db.execute(
                select(Instrument).where(Instrument.id == alert.instrument_id)
            ).scalar_one_or_none()
            symbol = instrument.symbol if instrument else None
        return self._serialize_alert(alert, symbol)

    def delete_alert(self, user_id: str, alert_id: str) -> None:
        alert = self.db.execute(
            select(Alert).where(Alert.id == alert_id, Alert.user_id == user_id)
        ).scalar_one_or_none()
        if alert is None:
            raise ValueError("Alert not found")

        event_ids = self.db.execute(
            select(AlertEvent.id).where(AlertEvent.alert_id == alert.id)
        ).scalars().all()
        if event_ids:
            self.db.execute(delete(Notification).where(Notification.alert_event_id.in_(event_ids)))
            self.db.execute(delete(AlertEvent).where(AlertEvent.id.in_(event_ids)))

        self.db.delete(alert)
        self.db.commit()

    def list_events(self, user_id: str, limit: int = 200) -> list[dict[str, Any]]:
        rows = self.db.execute(
            select(AlertEvent, Alert, Instrument.symbol)
            .join(Alert, Alert.id == AlertEvent.alert_id)
            .join(Instrument, Instrument.id == Alert.instrument_id, isouter=True)
            .where(Alert.user_id == user_id)
            .order_by(AlertEvent.triggered_at.desc())
            .limit(limit)
        ).all()

        events: list[dict[str, Any]] = []
        for event, alert, symbol in rows:
            events.append(
                {
                    "id": event.id,
                    "alert_id": alert.id,
                    "symbol": symbol,
                    "triggered_at": event.triggered_at,
                    "explanation": event.explanation,
                    "severity": event.severity,
                    "payload": event.payload,
                }
            )
        return events

    def evaluate_due_alerts(
        self, user_id: str, *, now: datetime | None = None, limit: int = 200
    ) -> dict[str, Any]:
        evaluated_at = now or datetime.now(UTC)
        due_rows = self.db.execute(
            select(Alert, Instrument.symbol)
            .join(Instrument, Instrument.id == Alert.instrument_id, isouter=True)
            .where(
                Alert.user_id == user_id,
                Alert.status == "active",
                or_(Alert.next_eval_at.is_(None), Alert.next_eval_at <= evaluated_at),
            )
            .order_by(Alert.next_eval_at.asc(), Alert.created_at.asc())
            .limit(limit)
        ).all()

        symbols = sorted({symbol for _, symbol in due_rows if isinstance(symbol, str)})
        quote_map = {quote.symbol: quote for quote in self.provider.get_quotes(symbols)}

        evaluated_count = 0
        triggered_count = 0
        notifications_created = 0

        for alert, symbol in due_rows:
            evaluated_count += 1
            alert.last_eval_at = evaluated_at
            interval_minutes = self._bounded_int(alert.rule, "interval_minutes", 5, 1, 1440)
            alert.next_eval_at = evaluated_at + timedelta(minutes=interval_minutes)

            quote = quote_map.get(symbol) if isinstance(symbol, str) else None
            evaluation = self._evaluate_rule(alert=alert, symbol=symbol, quote=quote)
            if not evaluation.triggered:
                continue

            cooldown_minutes = self._bounded_int(alert.rule, "cooldown_minutes", 60, 1, 1440)
            if self._is_in_cooldown(alert.id, evaluated_at, cooldown_minutes):
                continue

            event = AlertEvent(
                alert_id=alert.id,
                triggered_at=evaluated_at,
                payload=evaluation.payload,
                explanation=evaluation.explanation,
                severity=evaluation.severity,
            )
            self.db.add(event)
            self.db.flush()

            notification = Notification(
                user_id=user_id,
                alert_event_id=event.id,
                channel="in_app",
                title=f"Alert triggered: {symbol or 'MARKET'}",
                body=evaluation.explanation,
                status="sent",
            )
            self.db.add(notification)
            triggered_count += 1
            notifications_created += 1

        self.db.commit()
        return {
            "evaluated_count": evaluated_count,
            "triggered_count": triggered_count,
            "notifications_created": notifications_created,
            "evaluated_at": evaluated_at,
        }

    def list_notifications(
        self,
        user_id: str,
        *,
        status: str = "all",
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        if status == "unread":
            stmt = stmt.where(Notification.read_at.is_(None))
        elif status != "all":
            stmt = stmt.where(Notification.status == status)

        notifications = self.db.execute(stmt).scalars().all()
        return [self._serialize_notification(item) for item in notifications]

    def mark_notification_read(self, user_id: str, notification_id: str) -> dict[str, Any]:
        notification = self.db.execute(
            select(Notification).where(Notification.id == notification_id, Notification.user_id == user_id)
        ).scalar_one_or_none()
        if notification is None:
            raise ValueError("Notification not found")

        notification.read_at = datetime.now(UTC)
        notification.status = "read"
        self.db.commit()
        return {
            "id": notification.id,
            "status": notification.status,
            "read_at": notification.read_at,
        }

    def _serialize_alert(self, alert: Alert, symbol: str | None) -> dict[str, Any]:
        return {
            "id": alert.id,
            "symbol": symbol,
            "alert_type": alert.alert_type,
            "rule": alert.rule,
            "status": alert.status,
            "next_eval_at": alert.next_eval_at,
            "last_eval_at": alert.last_eval_at,
            "created_at": alert.created_at,
            "updated_at": alert.updated_at,
        }

    def _serialize_notification(self, notification: Notification) -> dict[str, Any]:
        return {
            "id": notification.id,
            "title": notification.title,
            "body": notification.body,
            "status": notification.status,
            "channel": notification.channel,
            "read_at": notification.read_at,
            "created_at": notification.created_at,
            "alert_event_id": notification.alert_event_id,
            "daily_brief_id": notification.daily_brief_id,
        }

    def _evaluate_rule(self, alert: Alert, symbol: str | None, quote: Quote | None) -> RuleEvaluation:
        if symbol is None or quote is None:
            return RuleEvaluation(
                triggered=False,
                explanation=f"No quote data available for {symbol or 'market alert'}.",
                severity="info",
                payload={"symbol": symbol, "reason": "missing_quote"},
            )

        if alert.alert_type == "price_threshold":
            target = self._to_float(alert.rule.get("target"))
            if target is None:
                return RuleEvaluation(
                    triggered=False,
                    explanation="Alert rule is missing a numeric target.",
                    severity="info",
                    payload={"symbol": symbol, "reason": "invalid_rule"},
                )

            operator = str(alert.rule.get("operator", ">="))
            triggered = self._compare(operator, quote.price, target)
            pct_gap = abs(quote.price - target) / max(target, 1.0)
            severity = "high" if pct_gap >= 0.03 else "medium"
            explanation = (
                f"{symbol} price {quote.price:.2f} {operator} threshold {target:.2f}."
                if triggered
                else f"{symbol} price {quote.price:.2f} did not meet {operator} {target:.2f}."
            )
            return RuleEvaluation(
                triggered=triggered,
                explanation=explanation,
                severity=severity,
                payload={
                    "symbol": symbol,
                    "price": round(quote.price, 6),
                    "target": target,
                    "operator": operator,
                },
            )

        if alert.alert_type == "percent_move":
            target = self._to_float(alert.rule.get("target"))
            if target is None:
                return RuleEvaluation(
                    triggered=False,
                    explanation="Percent-move alert rule is missing a numeric target.",
                    severity="info",
                    payload={"symbol": symbol, "reason": "invalid_rule"},
                )
            operator = str(alert.rule.get("operator", ">="))
            absolute = bool(alert.rule.get("absolute", True))
            observed = abs(quote.change_percent) if absolute else quote.change_percent
            triggered = self._compare(operator, observed, target)
            severity = "high" if abs(observed) >= max(target, 1.0) * 1.5 else "medium"
            return RuleEvaluation(
                triggered=triggered,
                explanation=(
                    f"{symbol} move {observed:.2f}% {operator} {target:.2f}%."
                    if triggered
                    else f"{symbol} move {observed:.2f}% did not meet {operator} {target:.2f}%."
                ),
                severity=severity,
                payload={
                    "symbol": symbol,
                    "change_percent": round(quote.change_percent, 6),
                    "observed_value": round(observed, 6),
                    "target": target,
                    "operator": operator,
                    "absolute": absolute,
                },
            )

        return RuleEvaluation(
            triggered=False,
            explanation=f"Unsupported alert type '{alert.alert_type}'.",
            severity="info",
            payload={"symbol": symbol, "reason": "unsupported_alert_type", "alert_type": alert.alert_type},
        )

    def _is_in_cooldown(self, alert_id: str, now: datetime, cooldown_minutes: int) -> bool:
        last_triggered_at = self.db.execute(
            select(AlertEvent.triggered_at)
            .where(AlertEvent.alert_id == alert_id)
            .order_by(AlertEvent.triggered_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        if last_triggered_at is None:
            return False
        return last_triggered_at >= now - timedelta(minutes=cooldown_minutes)

    def _bounded_int(
        self, rule: dict[str, Any], key: str, default: int, minimum: int, maximum: int
    ) -> int:
        raw_value = rule.get(key)
        if not isinstance(raw_value, int):
            return default
        if raw_value < minimum:
            return minimum
        if raw_value > maximum:
            return maximum
        return raw_value

    def _to_float(self, value: Any) -> float | None:
        if isinstance(value, int | float):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return None
        return None

    def _compare(self, operator: str, left: float, right: float) -> bool:
        if operator == ">":
            return left > right
        if operator == ">=":
            return left >= right
        if operator == "<":
            return left < right
        if operator == "<=":
            return left <= right
        if operator == "==":
            return abs(left - right) < 1e-9
        return False
