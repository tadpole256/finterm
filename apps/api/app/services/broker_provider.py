from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
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


class BrokerProvider(Protocol):
    def provider_name(self) -> str: ...

    def list_accounts(self, user_id: str) -> list[BrokerAccountRecord]: ...

    def list_positions(self, user_id: str, external_account_id: str) -> list[BrokerPositionRecord]: ...


class MockBrokerProvider(BrokerProvider):
    def provider_name(self) -> str:
        return "mock_broker"

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


def broker_provider_from_name(name: str) -> BrokerProvider:
    normalized = name.lower().strip()
    if normalized in {"mock", "mock_broker", "broker"}:
        return MockBrokerProvider()
    raise ValueError(f"Unsupported broker provider '{name}'")
