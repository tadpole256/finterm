from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import (
    BrokerAccount,
    BrokerPositionSnapshot,
    BrokerSyncRun,
    Instrument,
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
    ) -> None:
        self.db = db
        self.broker_provider = broker_provider
        self.market_provider = market_provider

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
            run.details = {"mode": "read_only", "provider": self.broker_provider.provider_name()}
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
                "message": "Broker sync completed (read-only).",
            }
        except Exception as exc:
            run.status = "failed"
            run.fetched_accounts = fetched_accounts
            run.fetched_positions = fetched_positions
            run.completed_at = datetime.now(UTC)
            run.error_message = str(exc)
            run.details = {"mode": "read_only", "provider": self.broker_provider.provider_name()}
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

    def reconcile(self, user_id: str, portfolio_id: str | None = None) -> dict[str, object]:
        local_positions_payload = PortfolioService(self.db, self.market_provider).positions(
            user_id=user_id,
            portfolio_id=portfolio_id,
        )
        local_holdings_raw = local_positions_payload.get("holdings")
        local_holdings = (
            local_holdings_raw
            if isinstance(local_holdings_raw, list)
            else []
        )
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
