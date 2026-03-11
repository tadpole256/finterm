from __future__ import annotations

import pytest

from app.services.portfolio_math import TransactionInput, compute_position


def test_compute_position_buy_buy_sell() -> None:
    result = compute_position(
        [
            TransactionInput(side="buy", quantity=10, price=100, fees=1),
            TransactionInput(side="buy", quantity=5, price=120, fees=1),
            TransactionInput(side="sell", quantity=6, price=130, fees=1),
        ]
    )

    assert result.quantity == 9.0
    assert result.avg_cost == pytest.approx(106.8)
    assert result.realized_pnl == pytest.approx(138.2)


def test_compute_position_rejects_oversell() -> None:
    with pytest.raises(ValueError, match="Sell quantity exceeds current position"):
        compute_position(
            [
                TransactionInput(side="buy", quantity=2, price=100, fees=0),
                TransactionInput(side="sell", quantity=3, price=110, fees=0),
            ]
        )


def test_compute_position_rejects_unknown_side() -> None:
    with pytest.raises(ValueError, match="Unsupported transaction side"):
        compute_position([TransactionInput(side="hold", quantity=1, price=10, fees=0)])
