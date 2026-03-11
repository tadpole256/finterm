from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import (
    Instrument,
    Portfolio,
    Position,
    ResearchNote,
    Thesis,
    Transaction,
    Watchlist,
    WatchlistItem,
)
from app.schemas.portfolio import CreateTransactionRequest
from app.services.market_provider import MarketDataProvider
from app.services.portfolio_math import PositionComputation, TransactionInput, compute_position


class PortfolioService:
    def __init__(self, db: Session, provider: MarketDataProvider) -> None:
        self.db = db
        self.provider = provider

    def overview(self, user_id: str, portfolio_id: str | None = None) -> dict[str, object]:
        portfolio = self._portfolio_for_user(user_id, portfolio_id)
        holdings, as_of, _ = self._positions_for_portfolio(user_id, portfolio)
        transactions = self._serialize_transactions(portfolio)

        market_value = sum(self._value_as_float(item.get("market_value")) for item in holdings)
        cost_basis = sum(self._value_as_float(item.get("cost_basis")) for item in holdings)
        unrealized = sum(self._value_as_float(item.get("unrealized_pnl")) for item in holdings)
        realized = sum(self._value_as_float(item.get("realized_pnl")) for item in holdings)

        summary = {
            "market_value": round(market_value, 2),
            "cost_basis": round(cost_basis, 2),
            "unrealized_pnl": round(unrealized, 2),
            "realized_pnl": round(realized, 2),
            "total_pnl": round(unrealized + realized, 2),
            "position_count": len(holdings),
        }

        exposure_totals: dict[str, float] = defaultdict(float)
        for item in holdings:
            sector = self._value_as_str(item.get("sector")) or "Unclassified"
            exposure_totals[sector] += self._value_as_float(item.get("market_value"))

        exposures = []
        for sector, value in sorted(exposure_totals.items(), key=lambda pair: pair[1], reverse=True):
            weight = value / market_value if market_value > 0 else 0.0
            exposures.append(
                {
                    "sector": sector,
                    "market_value": round(value, 2),
                    "weight": round(weight, 4),
                }
            )

        return {
            "portfolio": self._serialize_portfolio(portfolio),
            "as_of": as_of,
            "summary": summary,
            "holdings": holdings,
            "exposures": exposures,
            "transactions": transactions,
        }

    def positions(self, user_id: str, portfolio_id: str | None = None) -> dict[str, object]:
        portfolio = self._portfolio_for_user(user_id, portfolio_id)
        holdings, as_of, _ = self._positions_for_portfolio(user_id, portfolio)
        return {
            "portfolio": self._serialize_portfolio(portfolio),
            "as_of": as_of,
            "holdings": holdings,
        }

    def transactions(self, user_id: str, portfolio_id: str | None = None) -> dict[str, object]:
        portfolio = self._portfolio_for_user(user_id, portfolio_id)
        return {
            "portfolio": self._serialize_portfolio(portfolio),
            "transactions": self._serialize_transactions(portfolio),
        }

    def risk_snapshot(self, user_id: str, portfolio_id: str | None = None) -> dict[str, object]:
        portfolio = self._portfolio_for_user(user_id, portfolio_id)
        holdings, as_of, _ = self._positions_for_portfolio(user_id, portfolio)

        gross_market_value = sum(max(self._value_as_float(item.get("market_value")), 0.0) for item in holdings)
        if gross_market_value <= 0:
            return {
                "portfolio": self._serialize_portfolio(portfolio),
                "as_of": as_of,
                "net_exposure": 0.0,
                "gross_exposure": 0.0,
                "concentration_hhi": 0.0,
                "top_positions": [],
                "factor_exposures": [],
                "scenarios": self._scenario_impacts([], 0.0),
            }

        top_positions_rows = sorted(
            holdings,
            key=lambda item: self._value_as_float(item.get("market_value")),
            reverse=True,
        )[:5]
        top_positions = [
            {
                "symbol": str(item.get("symbol")),
                "market_value": round(self._value_as_float(item.get("market_value")), 2),
                "weight": round(self._value_as_float(item.get("market_value")) / gross_market_value, 4),
            }
            for item in top_positions_rows
        ]

        weights = [
            self._value_as_float(item.get("market_value")) / gross_market_value
            for item in holdings
            if self._value_as_float(item.get("market_value")) > 0
        ]
        concentration_hhi = round(sum(weight * weight for weight in weights), 4)

        factor_totals: dict[str, float] = defaultdict(float)
        for item in holdings:
            weight = self._value_as_float(item.get("market_value")) / gross_market_value
            if weight <= 0:
                continue
            for factor, score in self._factor_scores_for_holding(item).items():
                factor_totals[factor] += weight * score

        factor_exposures = [
            {
                "factor": factor,
                "exposure": round(value, 4),
                "method": "heuristic_sector_bucket_v1",
            }
            for factor, value in sorted(
                factor_totals.items(), key=lambda pair: abs(pair[1]), reverse=True
            )
        ]

        long_exposure = sum(max(self._value_as_float(item.get("market_value")), 0.0) for item in holdings)
        short_exposure = sum(abs(min(self._value_as_float(item.get("market_value")), 0.0)) for item in holdings)
        net_exposure_ratio = (long_exposure - short_exposure) / gross_market_value if gross_market_value > 0 else 0.0
        gross_exposure_ratio = (long_exposure + short_exposure) / gross_market_value if gross_market_value > 0 else 0.0

        return {
            "portfolio": self._serialize_portfolio(portfolio),
            "as_of": as_of,
            "net_exposure": round(net_exposure_ratio, 4),
            "gross_exposure": round(gross_exposure_ratio, 4),
            "concentration_hhi": concentration_hhi,
            "top_positions": top_positions,
            "factor_exposures": factor_exposures[:8],
            "scenarios": self._scenario_impacts(holdings, gross_market_value),
        }

    def create_transaction(self, user_id: str, payload: CreateTransactionRequest) -> dict[str, object]:
        portfolio = self._portfolio_for_user(user_id, payload.portfolio_id)
        instrument = self.db.execute(
            select(Instrument).where(Instrument.symbol == payload.symbol.upper())
        ).scalar_one_or_none()
        if instrument is None:
            raise ValueError(f"Unknown instrument symbol {payload.symbol}")

        txn = Transaction(
            portfolio_id=portfolio.id,
            instrument_id=instrument.id,
            trade_date=payload.trade_date or datetime.now(UTC),
            side=payload.side,
            quantity=Decimal(str(payload.quantity)),
            price=Decimal(str(payload.price)),
            fees=Decimal(str(payload.fees)),
            notes=payload.notes,
        )
        self.db.add(txn)
        self.db.commit()

        self._sync_positions(portfolio)

        return self._serialize_transaction_row(txn, instrument.symbol)

    def delete_transaction(self, user_id: str, transaction_id: str) -> None:
        txn = self.db.execute(
            select(Transaction)
            .join(Portfolio, Portfolio.id == Transaction.portfolio_id)
            .where(Transaction.id == transaction_id, Portfolio.user_id == user_id)
        ).scalar_one_or_none()

        if txn is None:
            raise ValueError("Transaction not found")

        portfolio = self.db.execute(select(Portfolio).where(Portfolio.id == txn.portfolio_id)).scalar_one()
        self.db.delete(txn)
        self.db.commit()

        self._sync_positions(portfolio)

    def _portfolio_for_user(self, user_id: str, portfolio_id: str | None) -> Portfolio:
        if portfolio_id:
            portfolio = self.db.execute(
                select(Portfolio).where(Portfolio.id == portfolio_id, Portfolio.user_id == user_id)
            ).scalar_one_or_none()
            if portfolio is None:
                raise ValueError("Portfolio not found")
            return portfolio

        portfolio = self.db.execute(
            select(Portfolio).where(Portfolio.user_id == user_id).order_by(Portfolio.created_at.asc())
        ).scalar_one_or_none()

        if portfolio is not None:
            return portfolio

        portfolio = Portfolio(user_id=user_id, name="Personal", base_currency="USD")
        self.db.add(portfolio)
        self.db.commit()
        self.db.refresh(portfolio)
        return portfolio

    def _serialize_portfolio(self, portfolio: Portfolio) -> dict[str, object]:
        return {"id": portfolio.id, "name": portfolio.name, "base_currency": portfolio.base_currency}

    def _serialize_transactions(self, portfolio: Portfolio, limit: int = 80) -> list[dict[str, object]]:
        rows = self.db.execute(
            select(Transaction, Instrument.symbol)
            .join(Instrument, Instrument.id == Transaction.instrument_id)
            .where(Transaction.portfolio_id == portfolio.id)
            .order_by(Transaction.trade_date.desc(), Transaction.created_at.desc())
            .limit(limit)
        ).all()

        return [self._serialize_transaction_row(txn, symbol) for txn, symbol in rows]

    def _serialize_transaction_row(self, txn: Transaction, symbol: str) -> dict[str, object]:
        quantity = float(txn.quantity)
        price = float(txn.price)
        return {
            "id": txn.id,
            "symbol": symbol,
            "trade_date": txn.trade_date,
            "side": txn.side,
            "quantity": quantity,
            "price": price,
            "fees": float(txn.fees),
            "notional": round(quantity * price, 2),
            "notes": txn.notes,
        }

    def _positions_for_portfolio(
        self,
        user_id: str,
        portfolio: Portfolio,
    ) -> tuple[list[dict[str, object]], datetime, dict[str, PositionComputation]]:
        calculations = self._sync_positions(portfolio)
        as_of = datetime.now(UTC)

        rows = self.db.execute(
            select(Position, Instrument)
            .join(Instrument, Instrument.id == Position.instrument_id)
            .where(Position.portfolio_id == portfolio.id)
            .order_by(Instrument.symbol.asc())
        ).all()

        if not rows:
            return [], as_of, calculations

        instrument_ids = [instrument.id for _, instrument in rows]

        note_counts_rows = self.db.execute(
            select(ResearchNote.instrument_id, func.count(ResearchNote.id))
            .where(
                ResearchNote.user_id == user_id,
                ResearchNote.instrument_id.in_(instrument_ids),
            )
            .group_by(ResearchNote.instrument_id)
        ).all()
        note_counts = {instrument_id: int(count) for instrument_id, count in note_counts_rows}

        thesis_counts_rows = self.db.execute(
            select(Thesis.instrument_id, func.count(Thesis.id))
            .where(
                Thesis.user_id == user_id,
                Thesis.status == "active",
                Thesis.instrument_id.in_(instrument_ids),
            )
            .group_by(Thesis.instrument_id)
        ).all()
        thesis_counts = {instrument_id: int(count) for instrument_id, count in thesis_counts_rows}

        watchlist_rows = self.db.execute(
            select(WatchlistItem.instrument_id, Watchlist.name)
            .join(Watchlist, Watchlist.id == WatchlistItem.watchlist_id)
            .where(
                Watchlist.user_id == user_id,
                WatchlistItem.instrument_id.in_(instrument_ids),
            )
            .order_by(Watchlist.name.asc())
        ).all()
        watchlist_map: dict[str, list[str]] = defaultdict(list)
        for instrument_id, watchlist_name in watchlist_rows:
            watchlist_map[instrument_id].append(watchlist_name)

        holdings: list[dict[str, object]] = []
        for position, instrument in rows:
            symbol = instrument.symbol
            calc = calculations.get(symbol)
            quantity = float(position.quantity)
            avg_cost = float(position.avg_cost)
            market_value = float(position.market_value) if position.market_value is not None else None
            cost_basis = round(quantity * avg_cost, 2)
            unrealized = round((market_value - cost_basis), 2) if market_value is not None else None

            holdings.append(
                {
                    "instrument_id": instrument.id,
                    "symbol": symbol,
                    "name": instrument.name,
                    "sector": instrument.sector,
                    "quantity": quantity,
                    "avg_cost": avg_cost,
                    "last_price": float(position.last_price) if position.last_price is not None else None,
                    "market_value": round(market_value, 2) if market_value is not None else None,
                    "cost_basis": cost_basis,
                    "unrealized_pnl": unrealized,
                    "realized_pnl": round(calc.realized_pnl if calc else 0.0, 2),
                    "note_count": note_counts.get(instrument.id, 0),
                    "active_thesis_count": thesis_counts.get(instrument.id, 0),
                    "watchlists": watchlist_map.get(instrument.id, []),
                }
            )

        return holdings, as_of, calculations

    def _sync_positions(self, portfolio: Portfolio) -> dict[str, PositionComputation]:
        txn_rows = self.db.execute(
            select(Transaction, Instrument)
            .join(Instrument, Instrument.id == Transaction.instrument_id)
            .where(Transaction.portfolio_id == portfolio.id)
            .order_by(Transaction.instrument_id.asc(), Transaction.trade_date.asc(), Transaction.created_at.asc())
        ).all()

        grouped: dict[str, list[TransactionInput]] = defaultdict(list)
        symbol_by_instrument_id: dict[str, str] = {}
        instrument_by_symbol: dict[str, Instrument] = {}

        for txn, instrument in txn_rows:
            grouped[instrument.id].append(
                TransactionInput(
                    side=txn.side,
                    quantity=float(txn.quantity),
                    price=float(txn.price),
                    fees=float(txn.fees),
                )
            )
            symbol_by_instrument_id[instrument.id] = instrument.symbol
            instrument_by_symbol[instrument.symbol] = instrument

        calculations: dict[str, PositionComputation] = {}
        for instrument_id, txns in grouped.items():
            symbol = symbol_by_instrument_id[instrument_id]
            calculations[symbol] = compute_position(txns)

        symbols = sorted(calculations.keys())
        quotes = {quote.symbol: quote for quote in self.provider.get_quotes(symbols)}

        existing_positions = self.db.execute(
            select(Position).where(Position.portfolio_id == portfolio.id)
        ).scalars().all()
        by_instrument_id = {position.instrument_id: position for position in existing_positions}

        now = datetime.now(UTC)

        for symbol, calc in calculations.items():
            instrument = instrument_by_symbol[symbol]
            position = by_instrument_id.get(instrument.id)
            quote = quotes.get(symbol)

            if calc.quantity <= 0:
                if position is not None:
                    self.db.delete(position)
                continue

            last_price = quote.price if quote is not None else None
            market_value = calc.quantity * last_price if last_price is not None else None
            quantity_decimal = Decimal(str(calc.quantity))
            avg_cost_decimal = Decimal(str(calc.avg_cost))
            last_price_decimal = Decimal(str(last_price)) if last_price is not None else None
            market_value_decimal = Decimal(str(market_value)) if market_value is not None else None

            if position is None:
                position = Position(
                    portfolio_id=portfolio.id,
                    instrument_id=instrument.id,
                    quantity=quantity_decimal,
                    avg_cost=avg_cost_decimal,
                    last_price=last_price_decimal,
                    market_value=market_value_decimal,
                    as_of=now,
                )
                self.db.add(position)
            else:
                position.quantity = quantity_decimal
                position.avg_cost = avg_cost_decimal
                position.last_price = last_price_decimal
                position.market_value = market_value_decimal
                position.as_of = now

        self.db.commit()
        return calculations

    @staticmethod
    def _value_as_float(value: object | None) -> float:
        if isinstance(value, int | float):
            return float(value)
        return 0.0

    @staticmethod
    def _value_as_str(value: object | None) -> str | None:
        if isinstance(value, str):
            return value
        return None

    def _factor_scores_for_holding(self, holding: dict[str, object]) -> dict[str, float]:
        symbol = str(holding.get("symbol") or "").upper()
        sector = str(holding.get("sector") or "").lower()

        if symbol in {"SPY", "QQQ", "IWM", "DIA"}:
            return {"market_beta": 1.0, "growth": 0.4}

        if "technology" in sector:
            return {"growth": 0.95, "quality": 0.45, "duration_risk": 0.75}
        if "financial" in sector:
            return {"value": 0.75, "rate_sensitivity": 0.8}
        if "health" in sector:
            return {"defensive": 0.65, "quality": 0.5}
        if "energy" in sector or "material" in sector:
            return {"inflation_beta": 0.7, "cyclicality": 0.65}
        if "utility" in sector or "consumer staple" in sector:
            return {"defensive": 0.85}

        return {"market_beta": 0.6}

    def _scenario_impacts(
        self,
        holdings: list[dict[str, object]],
        gross_market_value: float,
    ) -> list[dict[str, object]]:
        scenarios: list[tuple[str, str, float, dict[str, float]]] = [
            (
                "Risk-Off Growth Shock",
                "Technology -12%, Consumer Discretionary -10%, all others -6%.",
                -0.06,
                {
                    "technology": -0.12,
                    "consumer discretionary": -0.10,
                },
            ),
            (
                "Rates +100bp",
                "Technology -8%, Real Estate -10%, Financials +4%, all others -3%.",
                -0.03,
                {
                    "technology": -0.08,
                    "real estate": -0.10,
                    "financial": 0.04,
                },
            ),
            (
                "Soft Landing Risk-On",
                "Technology +7%, Financials +5%, Healthcare +3%, all others +4%.",
                0.04,
                {
                    "technology": 0.07,
                    "financial": 0.05,
                    "health": 0.03,
                },
            ),
        ]

        rows: list[dict[str, object]] = []
        for name, assumptions, default_shock, shocks in scenarios:
            estimated_pnl = 0.0
            for holding in holdings:
                market_value = self._value_as_float(holding.get("market_value"))
                if market_value == 0:
                    continue
                sector = str(holding.get("sector") or "").lower()
                shock = default_shock
                for sector_term, sector_shock in shocks.items():
                    if sector_term in sector:
                        shock = sector_shock
                        break
                estimated_pnl += market_value * shock

            estimated_return = estimated_pnl / gross_market_value if gross_market_value > 0 else 0.0
            rows.append(
                {
                    "name": name,
                    "estimated_pnl": round(estimated_pnl, 2),
                    "estimated_return": round(estimated_return, 4),
                    "assumptions": assumptions,
                }
            )

        return rows
