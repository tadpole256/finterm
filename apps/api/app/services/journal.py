from __future__ import annotations

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.db.models import (
    BrokerOrderEvent,
    Portfolio,
    TradeJournalEntry,
    Transaction,
)
from app.schemas.journal import CreateTradeJournalEntryRequest


class JournalService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_entries(
        self,
        user_id: str,
        *,
        symbol: str | None = None,
        entry_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, object]]:
        stmt = (
            select(TradeJournalEntry)
            .where(TradeJournalEntry.user_id == user_id)
            .order_by(TradeJournalEntry.created_at.desc())
            .limit(max(1, min(limit, 250)))
        )
        if symbol:
            stmt = stmt.where(TradeJournalEntry.symbol == symbol.upper())
        if entry_type:
            stmt = stmt.where(TradeJournalEntry.entry_type == entry_type)

        rows = self.db.execute(stmt).scalars().all()
        return [self._serialize_entry(row) for row in rows]

    def create_entry(
        self,
        user_id: str,
        payload: CreateTradeJournalEntryRequest,
    ) -> dict[str, object]:
        symbol = payload.symbol.upper() if payload.symbol else None
        portfolio_id = payload.portfolio_id
        transaction_id = payload.transaction_id
        broker_order_event_id = payload.broker_order_event_id

        if transaction_id:
            transaction = self.db.execute(
                select(Transaction)
                .join(Portfolio, Portfolio.id == Transaction.portfolio_id)
                .where(
                    and_(
                        Transaction.id == transaction_id,
                        Portfolio.user_id == user_id,
                    )
                )
            ).scalar_one_or_none()
            if transaction is None:
                raise ValueError("Transaction not found for user")
            portfolio_id = portfolio_id or transaction.portfolio_id

        if broker_order_event_id:
            order_event = self.db.execute(
                select(BrokerOrderEvent).where(
                    BrokerOrderEvent.id == broker_order_event_id,
                    BrokerOrderEvent.user_id == user_id,
                )
            ).scalar_one_or_none()
            if order_event is None:
                raise ValueError("Broker order event not found for user")
            if symbol is None:
                symbol = order_event.symbol

        entry = TradeJournalEntry(
            user_id=user_id,
            symbol=symbol,
            entry_type=payload.entry_type,
            title=payload.title,
            body=payload.body,
            tags=payload.tags,
            portfolio_id=portfolio_id,
            transaction_id=transaction_id,
            broker_order_event_id=broker_order_event_id,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return self._serialize_entry(entry)

    @staticmethod
    def _serialize_entry(entry: TradeJournalEntry) -> dict[str, object]:
        return {
            "id": entry.id,
            "symbol": entry.symbol,
            "entry_type": entry.entry_type,
            "title": entry.title,
            "body": entry.body,
            "tags": entry.tags,
            "portfolio_id": entry.portfolio_id,
            "transaction_id": entry.transaction_id,
            "broker_order_event_id": entry.broker_order_event_id,
            "created_at": entry.created_at,
            "updated_at": entry.updated_at,
        }
