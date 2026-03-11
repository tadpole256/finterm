from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class TransactionInput:
    side: str
    quantity: float
    price: float
    fees: float


@dataclass(slots=True)
class PositionComputation:
    quantity: float
    avg_cost: float
    realized_pnl: float


def compute_position(transactions: list[TransactionInput]) -> PositionComputation:
    quantity = 0.0
    avg_cost = 0.0
    realized_pnl = 0.0

    for txn in transactions:
        side = txn.side.lower()

        if side == "buy":
            previous_cost = quantity * avg_cost
            new_cost = txn.quantity * txn.price + txn.fees
            quantity += txn.quantity
            if quantity <= 0:
                raise ValueError("Invalid quantity after buy transaction")
            avg_cost = (previous_cost + new_cost) / quantity
            continue

        if side == "sell":
            if txn.quantity > quantity + 1e-9:
                raise ValueError("Sell quantity exceeds current position")

            proceeds = txn.quantity * txn.price - txn.fees
            cost_basis = txn.quantity * avg_cost
            realized_pnl += proceeds - cost_basis
            quantity -= txn.quantity

            if quantity <= 1e-9:
                quantity = 0.0
                avg_cost = 0.0
            continue

        raise ValueError(f"Unsupported transaction side '{txn.side}'")

    return PositionComputation(
        quantity=round(quantity, 8),
        avg_cost=round(avg_cost, 8),
        realized_pnl=round(realized_pnl, 8),
    )
