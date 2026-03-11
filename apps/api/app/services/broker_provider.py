from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol


@dataclass(slots=True)
class BrokerAccountRecord:
    external_account_id: str
    account_name: str
    account_type: str
    base_currency: str
    status: str
    account_meta: dict[str, object]


@dataclass(slots=True)
class BrokerPositionRecord:
    external_account_id: str
    symbol: str
    quantity: float
    avg_cost: float | None
    market_price: float | None
    market_value: float | None
    as_of: datetime


@dataclass(slots=True)
class BrokerCapabilities:
    provider: str
    supports_positions: bool
    supports_order_preview: bool
    supports_order_submission: bool
    supports_reconciliation: bool
    requires_auth: bool
    trading_enabled: bool
    can_submit_orders: bool
    restrictions: list[str]


@dataclass(slots=True)
class BrokerSessionState:
    provider: str
    connected: bool
    auth_state: str
    last_refreshed_at: datetime
    expires_at: datetime | None


@dataclass(slots=True)
class BrokerOrderPreview:
    provider: str
    symbol: str
    side: str
    order_type: str
    quantity: float
    reference_price: float
    estimated_notional: float
    estimated_fees: float
    estimated_total_cash: float
    can_submit: bool
    restrictions: list[str]
    warnings: list[str]


class BrokerProvider(Protocol):
    def provider_name(self) -> str: ...

    def capabilities(self, *, trading_enabled: bool) -> BrokerCapabilities: ...

    def session_state(self, user_id: str) -> BrokerSessionState: ...

    def list_accounts(self, user_id: str) -> list[BrokerAccountRecord]: ...

    def list_positions(self, user_id: str, external_account_id: str) -> list[BrokerPositionRecord]: ...

    def preview_order(
        self,
        user_id: str,
        *,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        reference_price: float,
        limit_price: float | None = None,
        trading_enabled: bool,
    ) -> BrokerOrderPreview: ...


class MockBrokerProvider(BrokerProvider):
    def provider_name(self) -> str:
        return "mock_broker"

    def capabilities(self, *, trading_enabled: bool) -> BrokerCapabilities:
        restrictions: list[str] = []
        if not trading_enabled:
            restrictions.append("BROKER_TRADING_ENABLED is false.")

        return BrokerCapabilities(
            provider=self.provider_name(),
            supports_positions=True,
            supports_order_preview=True,
            supports_order_submission=True,
            supports_reconciliation=True,
            requires_auth=False,
            trading_enabled=trading_enabled,
            can_submit_orders=trading_enabled,
            restrictions=restrictions,
        )

    def session_state(self, user_id: str) -> BrokerSessionState:
        now = datetime.now(UTC)
        return BrokerSessionState(
            provider=self.provider_name(),
            connected=True,
            auth_state="simulated",
            last_refreshed_at=now,
            expires_at=now + timedelta(hours=8),
        )

    def list_accounts(self, user_id: str) -> list[BrokerAccountRecord]:
        return [
            BrokerAccountRecord(
                external_account_id="paper-main",
                account_name="Paper Main",
                account_type="taxable",
                base_currency="USD",
                status="active",
                account_meta={"connection": "simulated", "user_ref": user_id},
            )
        ]

    def list_positions(self, user_id: str, external_account_id: str) -> list[BrokerPositionRecord]:
        as_of = datetime.now(UTC)
        if external_account_id != "paper-main":
            return []
        return [
            BrokerPositionRecord(
                external_account_id=external_account_id,
                symbol="AAPL",
                quantity=42.0,
                avg_cost=197.25,
                market_price=219.15,
                market_value=9204.3,
                as_of=as_of,
            ),
            BrokerPositionRecord(
                external_account_id=external_account_id,
                symbol="MSFT",
                quantity=14.0,
                avg_cost=409.1,
                market_price=423.62,
                market_value=5930.68,
                as_of=as_of,
            ),
            BrokerPositionRecord(
                external_account_id=external_account_id,
                symbol="SPY",
                quantity=8.0,
                avg_cost=506.0,
                market_price=512.34,
                market_value=4098.72,
                as_of=as_of,
            ),
        ]

    def preview_order(
        self,
        user_id: str,
        *,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        reference_price: float,
        limit_price: float | None = None,
        trading_enabled: bool,
    ) -> BrokerOrderPreview:
        restrictions: list[str] = []
        warnings: list[str] = []
        if not trading_enabled:
            restrictions.append("Order submission disabled by configuration.")

        resolved_price = (
            float(limit_price)
            if order_type.lower() == "limit" and limit_price is not None
            else float(reference_price)
        )
        estimated_notional = resolved_price * quantity
        estimated_fees = max(1.0, estimated_notional * 0.0005)
        estimated_total_cash = estimated_notional + estimated_fees
        if side.lower() == "sell":
            estimated_total_cash = estimated_notional - estimated_fees
            warnings.append("Estimated proceeds ignore borrow and venue-specific charges.")

        if quantity > 10_000:
            warnings.append("Large quantity preview; check venue liquidity before submission.")

        return BrokerOrderPreview(
            provider=self.provider_name(),
            symbol=symbol.upper(),
            side=side.lower(),
            order_type=order_type.lower(),
            quantity=quantity,
            reference_price=resolved_price,
            estimated_notional=round(estimated_notional, 2),
            estimated_fees=round(estimated_fees, 2),
            estimated_total_cash=round(estimated_total_cash, 2),
            can_submit=trading_enabled,
            restrictions=restrictions,
            warnings=warnings,
        )


def broker_provider_from_name(name: str) -> BrokerProvider:
    normalized = name.lower().strip()
    if normalized in {"mock", "mock_broker", "broker"}:
        return MockBrokerProvider()
    raise ValueError(f"Unsupported broker provider '{name}'")
