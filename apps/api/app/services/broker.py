from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import (
    BrokerAccount,
    BrokerOrderEvent,
    BrokerPositionSnapshot,
    BrokerSyncRun,
    Instrument,
    ReconciliationException,
    TradeJournalEntry,
)
from app.services.broker_provider import BrokerProvider
from app.services.market_provider import MarketDataProvider
from app.services.portfolio import PortfolioService


class BrokerService:
    def __init__(
        self,
        db: Session,
        broker_provider: BrokerProvider,
        market_provider: MarketDataProvider,
        *,
        trading_enabled: bool = False,
    ) -> None:
        self.db = db
        self.broker_provider = broker_provider
        self.market_provider = market_provider
        self.trading_enabled = trading_enabled

    def capabilities(self, user_id: str) -> dict[str, object]:
        capabilities = self.broker_provider.capabilities(trading_enabled=self.trading_enabled)
        session = self.broker_provider.session_state(user_id)
        return {
            "capabilities": {
                "provider": capabilities.provider,
                "supports_positions": capabilities.supports_positions,
                "supports_order_preview": capabilities.supports_order_preview,
                "supports_order_submission": capabilities.supports_order_submission,
                "supports_reconciliation": capabilities.supports_reconciliation,
                "requires_auth": capabilities.requires_auth,
                "trading_enabled": capabilities.trading_enabled,
                "can_submit_orders": capabilities.can_submit_orders,
                "restrictions": capabilities.restrictions,
            },
            "session": {
                "provider": session.provider,
                "connected": session.connected,
                "auth_state": session.auth_state,
                "last_refreshed_at": session.last_refreshed_at,
                "expires_at": session.expires_at,
            },
        }

    def preview_order(
        self,
        user_id: str,
        *,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        limit_price: float | None = None,
    ) -> dict[str, object]:
        normalized_symbol = symbol.upper()
        quote = next(iter(self.market_provider.get_quotes([normalized_symbol])), None)

        reference_price = 0.0
        if quote is not None:
            reference_price = float(quote.price)
        elif limit_price is not None:
            reference_price = float(limit_price)

        if reference_price <= 0:
            raise ValueError(f"Unable to determine price for {normalized_symbol}")

        preview = self.broker_provider.preview_order(
            user_id=user_id,
            symbol=normalized_symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            reference_price=reference_price,
            limit_price=limit_price,
            trading_enabled=self.trading_enabled,
        )
        return {
            "provider": preview.provider,
            "symbol": preview.symbol,
            "side": preview.side,
            "order_type": preview.order_type,
            "quantity": preview.quantity,
            "reference_price": preview.reference_price,
            "estimated_notional": preview.estimated_notional,
            "estimated_fees": preview.estimated_fees,
            "estimated_total_cash": preview.estimated_total_cash,
            "can_submit": preview.can_submit,
            "restrictions": preview.restrictions,
            "warnings": preview.warnings,
        }

    def sync(self, user_id: str) -> dict[str, object]:
        started_at = datetime.now(UTC)
        run = BrokerSyncRun(
            user_id=user_id,
            provider=self.broker_provider.provider_name(),
            status="running",
            started_at=started_at,
            details={},
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)

        fetched_accounts = 0
        fetched_positions = 0

        try:
            accounts = self.broker_provider.list_accounts(user_id)
            fetched_accounts = len(accounts)
            for account_record in accounts:
                account = self.db.execute(
                    select(BrokerAccount).where(
                        BrokerAccount.user_id == user_id,
                        BrokerAccount.provider == self.broker_provider.provider_name(),
                        BrokerAccount.external_account_id == account_record.external_account_id,
                    )
                ).scalar_one_or_none()

                if account is None:
                    account = BrokerAccount(
                        user_id=user_id,
                        provider=self.broker_provider.provider_name(),
                        external_account_id=account_record.external_account_id,
                        account_name=account_record.account_name,
                        account_type=account_record.account_type,
                        base_currency=account_record.base_currency,
                        status=account_record.status,
                        account_meta=account_record.account_meta,
                        last_synced_at=started_at,
                    )
                    self.db.add(account)
                    self.db.flush()
                else:
                    account.account_name = account_record.account_name
                    account.account_type = account_record.account_type
                    account.base_currency = account_record.base_currency
                    account.status = account_record.status
                    account.account_meta = account_record.account_meta
                    account.last_synced_at = started_at

                self.db.execute(
                    delete(BrokerPositionSnapshot).where(
                        BrokerPositionSnapshot.broker_account_id == account.id
                    )
                )

                positions = self.broker_provider.list_positions(user_id, account_record.external_account_id)
                fetched_positions += len(positions)
                if not positions:
                    continue

                symbols = sorted({item.symbol.upper() for item in positions})
                instrument_rows = self.db.execute(
                    select(Instrument).where(Instrument.symbol.in_(symbols))
                ).scalars().all()
                instrument_by_symbol = {instrument.symbol: instrument for instrument in instrument_rows}

                for position_record in positions:
                    symbol = position_record.symbol.upper()
                    instrument = instrument_by_symbol.get(symbol)
                    self.db.add(
                        BrokerPositionSnapshot(
                            broker_account_id=account.id,
                            instrument_id=instrument.id if instrument else None,
                            symbol=symbol,
                            quantity=Decimal(str(position_record.quantity)),
                            avg_cost=(
                                Decimal(str(position_record.avg_cost))
                                if position_record.avg_cost is not None
                                else None
                            ),
                            market_price=(
                                Decimal(str(position_record.market_price))
                                if position_record.market_price is not None
                                else None
                            ),
                            market_value=(
                                Decimal(str(position_record.market_value))
                                if position_record.market_value is not None
                                else None
                            ),
                            as_of=position_record.as_of,
                            source_provider=self.broker_provider.provider_name(),
                        )
                    )

            run.status = "completed"
            run.fetched_accounts = fetched_accounts
            run.fetched_positions = fetched_positions
            run.completed_at = datetime.now(UTC)
            run.error_message = None
            run.details = {
                "mode": "read_only_sync",
                "provider": self.broker_provider.provider_name(),
                "trading_enabled": self.trading_enabled,
            }
            self.db.commit()
            self.db.refresh(run)
            return {
                "run_id": run.id,
                "provider": run.provider,
                "status": run.status,
                "fetched_accounts": run.fetched_accounts,
                "fetched_positions": run.fetched_positions,
                "started_at": run.started_at,
                "completed_at": run.completed_at,
                "message": "Broker sync completed (positions + account snapshots).",
            }
        except Exception as exc:
            run.status = "failed"
            run.fetched_accounts = fetched_accounts
            run.fetched_positions = fetched_positions
            run.completed_at = datetime.now(UTC)
            run.error_message = str(exc)
            run.details = {
                "mode": "read_only_sync",
                "provider": self.broker_provider.provider_name(),
                "trading_enabled": self.trading_enabled,
            }
            self.db.commit()
            raise

    def list_accounts(self, user_id: str) -> list[dict[str, object]]:
        accounts = self.db.execute(
            select(BrokerAccount)
            .where(BrokerAccount.user_id == user_id)
            .order_by(BrokerAccount.created_at.asc())
        ).scalars().all()

        account_views: list[dict[str, object]] = []
        for account in accounts:
            positions = self.db.execute(
                select(BrokerPositionSnapshot)
                .where(BrokerPositionSnapshot.broker_account_id == account.id)
                .order_by(BrokerPositionSnapshot.symbol.asc())
            ).scalars().all()

            total_market_value = sum(
                float(item.market_value) if item.market_value is not None else 0.0 for item in positions
            )
            account_views.append(
                {
                    "id": account.id,
                    "provider": account.provider,
                    "external_account_id": account.external_account_id,
                    "account_name": account.account_name,
                    "account_type": account.account_type,
                    "base_currency": account.base_currency,
                    "status": account.status,
                    "last_synced_at": account.last_synced_at,
                    "account_meta": account.account_meta,
                    "position_count": len(positions),
                    "total_market_value": round(total_market_value, 2),
                }
            )
        return account_views

    def list_account_details(self, user_id: str) -> list[dict[str, object]]:
        details: list[dict[str, object]] = []
        for account in self.list_accounts(user_id):
            rows = self.db.execute(
                select(BrokerPositionSnapshot)
                .where(BrokerPositionSnapshot.broker_account_id == account["id"])
                .order_by(BrokerPositionSnapshot.symbol.asc())
            ).scalars().all()

            positions = [
                {
                    "symbol": row.symbol,
                    "quantity": float(row.quantity),
                    "avg_cost": float(row.avg_cost) if row.avg_cost is not None else None,
                    "market_price": float(row.market_price) if row.market_price is not None else None,
                    "market_value": float(row.market_value) if row.market_value is not None else None,
                    "as_of": row.as_of,
                }
                for row in rows
            ]
            details.append({**account, "positions": positions})
        return details

    def record_order_event(
        self,
        user_id: str,
        *,
        broker_account_id: str | None,
        external_order_id: str,
        symbol: str,
        side: str,
        order_type: str,
        status: str,
        quantity: float,
        limit_price: float | None,
        filled_quantity: float,
        avg_fill_price: float | None,
        status_updated_at: datetime | None,
        event_payload: dict[str, object],
        create_journal_entry: bool = True,
    ) -> dict[str, object]:
        if broker_account_id is not None:
            account = self.db.execute(
                select(BrokerAccount).where(
                    BrokerAccount.id == broker_account_id,
                    BrokerAccount.user_id == user_id,
                )
            ).scalar_one_or_none()
            if account is None:
                raise ValueError("Broker account not found for user")

        now = datetime.now(UTC)
        order_event = BrokerOrderEvent(
            user_id=user_id,
            broker_account_id=broker_account_id,
            external_order_id=external_order_id,
            symbol=symbol.upper(),
            side=side.lower(),
            order_type=order_type.lower(),
            status=status.lower(),
            quantity=Decimal(str(quantity)),
            limit_price=Decimal(str(limit_price)) if limit_price is not None else None,
            filled_quantity=Decimal(str(filled_quantity)),
            avg_fill_price=Decimal(str(avg_fill_price)) if avg_fill_price is not None else None,
            submitted_at=now,
            status_updated_at=status_updated_at or now,
            event_payload=event_payload,
        )
        self.db.add(order_event)
        self.db.flush()

        if create_journal_entry:
            self.db.add(
                TradeJournalEntry(
                    user_id=user_id,
                    broker_order_event_id=order_event.id,
                    symbol=order_event.symbol,
                    entry_type="broker_fill",
                    title=f"{order_event.symbol} {order_event.side.upper()} {order_event.status}",
                    body=(
                        f"External order {order_event.external_order_id} "
                        f"status={order_event.status} qty={float(order_event.quantity):.4f} "
                        f"filled={float(order_event.filled_quantity):.4f}."
                    ),
                    tags=["broker", "fill"],
                )
            )

        self.db.commit()
        self.db.refresh(order_event)
        return self._serialize_order_event(order_event)

    def list_order_events(
        self,
        user_id: str,
        *,
        symbol: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, object]]:
        stmt = (
            select(BrokerOrderEvent)
            .where(BrokerOrderEvent.user_id == user_id)
            .order_by(BrokerOrderEvent.submitted_at.desc())
            .limit(max(1, min(limit, 250)))
        )
        if symbol:
            stmt = stmt.where(BrokerOrderEvent.symbol == symbol.upper())
        if status:
            stmt = stmt.where(BrokerOrderEvent.status == status.lower())

        rows = self.db.execute(stmt).scalars().all()
        return [self._serialize_order_event(row) for row in rows]

    def reconcile(self, user_id: str, portfolio_id: str | None = None) -> dict[str, object]:
        local_positions_payload = PortfolioService(self.db, self.market_provider).positions(
            user_id=user_id,
            portfolio_id=portfolio_id,
        )
        local_holdings_raw = local_positions_payload.get("holdings")
        local_holdings = local_holdings_raw if isinstance(local_holdings_raw, list) else []

        portfolio_payload = local_positions_payload.get("portfolio")
        resolved_portfolio_id = portfolio_id
        if resolved_portfolio_id is None and isinstance(portfolio_payload, dict):
            payload_portfolio_id = portfolio_payload.get("id")
            if isinstance(payload_portfolio_id, str):
                resolved_portfolio_id = payload_portfolio_id

        local_by_symbol: dict[str, dict[str, object]] = {
            str(item["symbol"]).upper(): item
            for item in local_holdings
            if isinstance(item, dict) and isinstance(item.get("symbol"), str)
        }

        snapshots = self.db.execute(
            select(BrokerPositionSnapshot)
            .join(BrokerAccount, BrokerAccount.id == BrokerPositionSnapshot.broker_account_id)
            .where(BrokerAccount.user_id == user_id)
            .order_by(BrokerPositionSnapshot.as_of.desc())
        ).scalars().all()

        broker_by_symbol: dict[str, dict[str, float]] = defaultdict(
            lambda: {"quantity": 0.0, "market_value": 0.0}
        )
        as_of: datetime = datetime.now(UTC)
        for snapshot in snapshots:
            snapshot_as_of = self._ensure_aware(snapshot.as_of)
            as_of = max(as_of, snapshot_as_of)
            bucket = broker_by_symbol[snapshot.symbol.upper()]
            bucket["quantity"] += float(snapshot.quantity)
            bucket["market_value"] += float(snapshot.market_value) if snapshot.market_value is not None else 0.0

        local_symbols = set(local_by_symbol.keys())
        broker_symbols = set(broker_by_symbol.keys())

        only_local = sorted(local_symbols - broker_symbols)
        only_broker = sorted(broker_symbols - local_symbols)

        quantity_mismatches: list[dict[str, object]] = []
        for symbol in sorted(local_symbols & broker_symbols):
            local_quantity = self._numeric(local_by_symbol[symbol].get("quantity"))
            broker_quantity = broker_by_symbol[symbol].get("quantity") or 0.0
            delta = broker_quantity - local_quantity
            if abs(delta) < 1e-6:
                continue
            quantity_mismatches.append(
                {
                    "symbol": symbol,
                    "local_quantity": round(local_quantity, 6),
                    "broker_quantity": round(broker_quantity, 6),
                    "quantity_delta": round(delta, 6),
                    "local_market_value": self._to_float(local_by_symbol[symbol].get("market_value")),
                    "broker_market_value": round(
                        broker_by_symbol[symbol].get("market_value") or 0.0, 2
                    ),
                }
            )

        open_exception_count = self._sync_reconciliation_exceptions(
            user_id=user_id,
            portfolio_id=resolved_portfolio_id,
            only_local=only_local,
            only_broker=only_broker,
            quantity_mismatches=quantity_mismatches,
        )

        return {
            "as_of": as_of,
            "summary": {
                "local_symbol_count": len(local_symbols),
                "broker_symbol_count": len(broker_symbols),
                "only_local_count": len(only_local),
                "only_broker_count": len(only_broker),
                "quantity_mismatch_count": len(quantity_mismatches),
            },
            "only_local": only_local,
            "only_broker": only_broker,
            "quantity_mismatches": quantity_mismatches,
            "open_exception_count": open_exception_count,
        }

    def list_reconciliation_exceptions(
        self,
        user_id: str,
        *,
        status_filter: str = "open",
        limit: int = 100,
    ) -> list[dict[str, object]]:
        stmt = (
            select(ReconciliationException)
            .where(ReconciliationException.user_id == user_id)
            .order_by(ReconciliationException.last_seen_at.desc())
            .limit(max(1, min(limit, 300)))
        )
        if status_filter != "all":
            stmt = stmt.where(ReconciliationException.status == status_filter)

        rows = self.db.execute(stmt).scalars().all()
        return [self._serialize_exception(item) for item in rows]

    def resolve_reconciliation_exception(
        self,
        user_id: str,
        exception_id: str,
        resolution_note: str | None = None,
    ) -> dict[str, object]:
        row = self.db.execute(
            select(ReconciliationException).where(
                ReconciliationException.id == exception_id,
                ReconciliationException.user_id == user_id,
            )
        ).scalar_one_or_none()
        if row is None:
            raise ValueError("Reconciliation exception not found")

        row.status = "resolved"
        row.resolved_at = datetime.now(UTC)
        row.resolution_note = resolution_note or "Resolved by user."
        self.db.commit()
        self.db.refresh(row)
        return self._serialize_exception(row)

    def _sync_reconciliation_exceptions(
        self,
        *,
        user_id: str,
        portfolio_id: str | None,
        only_local: list[str],
        only_broker: list[str],
        quantity_mismatches: list[dict[str, object]],
    ) -> int:
        now = datetime.now(UTC)
        active_payload: dict[tuple[str, str], dict[str, object]] = {}

        for symbol in only_local:
            active_payload[("only_local", symbol)] = {
                "symbol": symbol,
                "issue_type": "only_local",
                "severity": "medium",
                "local_quantity": None,
                "broker_quantity": None,
                "local_market_value": None,
                "broker_market_value": None,
                "details": {},
            }

        for symbol in only_broker:
            active_payload[("only_broker", symbol)] = {
                "symbol": symbol,
                "issue_type": "only_broker",
                "severity": "medium",
                "local_quantity": None,
                "broker_quantity": None,
                "local_market_value": None,
                "broker_market_value": None,
                "details": {},
            }

        for row in quantity_mismatches:
            symbol = str(row["symbol"]).upper()
            delta_raw = row.get("quantity_delta")
            delta = float(delta_raw) if isinstance(delta_raw, int | float) else 0.0
            severity = "high" if abs(delta) >= 1 else "medium"
            active_payload[("quantity_mismatch", symbol)] = {
                "symbol": symbol,
                "issue_type": "quantity_mismatch",
                "severity": severity,
                "local_quantity": row.get("local_quantity"),
                "broker_quantity": row.get("broker_quantity"),
                "local_market_value": row.get("local_market_value"),
                "broker_market_value": row.get("broker_market_value"),
                "details": {"quantity_delta": delta},
            }

        existing_rows = self.db.execute(
            select(ReconciliationException).where(
                ReconciliationException.user_id == user_id,
                ReconciliationException.status.in_(["open", "acknowledged"]),
            )
        ).scalars().all()
        existing_by_key = {(row.issue_type, row.symbol.upper()): row for row in existing_rows}

        for key, payload in active_payload.items():
            existing = existing_by_key.get(key)
            if existing is None:
                self.db.add(
                    ReconciliationException(
                        user_id=user_id,
                        portfolio_id=portfolio_id,
                        symbol=str(payload["symbol"]),
                        issue_type=str(payload["issue_type"]),
                        severity=str(payload["severity"]),
                        status="open",
                        local_quantity=self._decimal_or_none(payload["local_quantity"]),
                        broker_quantity=self._decimal_or_none(payload["broker_quantity"]),
                        local_market_value=self._decimal_or_none(payload["local_market_value"]),
                        broker_market_value=self._decimal_or_none(payload["broker_market_value"]),
                        detected_at=now,
                        last_seen_at=now,
                        details=(payload["details"] if isinstance(payload["details"], dict) else {}),
                    )
                )
                continue

            existing.severity = str(payload["severity"])
            existing.last_seen_at = now
            existing.local_quantity = self._decimal_or_none(payload["local_quantity"])
            existing.broker_quantity = self._decimal_or_none(payload["broker_quantity"])
            existing.local_market_value = self._decimal_or_none(payload["local_market_value"])
            existing.broker_market_value = self._decimal_or_none(payload["broker_market_value"])
            existing.details = payload["details"] if isinstance(payload["details"], dict) else {}
            if existing.status == "resolved":
                existing.status = "open"
                existing.resolved_at = None
                existing.resolution_note = None

        active_keys = set(active_payload.keys())
        for key, existing in existing_by_key.items():
            if key in active_keys:
                continue
            existing.status = "resolved"
            existing.resolved_at = now
            if not existing.resolution_note:
                existing.resolution_note = "Auto-resolved by latest reconciliation."

        self.db.commit()

        open_count = self.db.execute(
            select(ReconciliationException)
            .where(
                ReconciliationException.user_id == user_id,
                ReconciliationException.status.in_(["open", "acknowledged"]),
            )
        ).scalars().all()
        return len(open_count)

    @staticmethod
    def _serialize_order_event(row: BrokerOrderEvent) -> dict[str, object]:
        return {
            "id": row.id,
            "broker_account_id": row.broker_account_id,
            "external_order_id": row.external_order_id,
            "symbol": row.symbol,
            "side": row.side,
            "order_type": row.order_type,
            "status": row.status,
            "quantity": float(row.quantity),
            "limit_price": float(row.limit_price) if row.limit_price is not None else None,
            "filled_quantity": float(row.filled_quantity),
            "avg_fill_price": float(row.avg_fill_price) if row.avg_fill_price is not None else None,
            "submitted_at": row.submitted_at,
            "status_updated_at": row.status_updated_at,
            "event_payload": row.event_payload,
        }

    @staticmethod
    def _serialize_exception(row: ReconciliationException) -> dict[str, object]:
        return {
            "id": row.id,
            "symbol": row.symbol,
            "issue_type": row.issue_type,
            "severity": row.severity,
            "status": row.status,
            "local_quantity": float(row.local_quantity) if row.local_quantity is not None else None,
            "broker_quantity": float(row.broker_quantity) if row.broker_quantity is not None else None,
            "local_market_value": float(row.local_market_value) if row.local_market_value is not None else None,
            "broker_market_value": float(row.broker_market_value) if row.broker_market_value is not None else None,
            "detected_at": row.detected_at,
            "last_seen_at": row.last_seen_at,
            "resolved_at": row.resolved_at,
            "resolution_note": row.resolution_note,
            "details": row.details,
        }

    @staticmethod
    def _to_float(value: object | None) -> float | None:
        if isinstance(value, int | float):
            return round(float(value), 2)
        return None

    @staticmethod
    def _numeric(value: object | None) -> float:
        if isinstance(value, int | float):
            return float(value)
        return 0.0

    @staticmethod
    def _ensure_aware(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value

    @staticmethod
    def _decimal_or_none(value: object | None) -> Decimal | None:
        if isinstance(value, int | float):
            return Decimal(str(value))
        return None
