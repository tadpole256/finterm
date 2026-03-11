from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from sqlalchemy import delete, select

from app.core.config import get_settings
from app.db.models import (
    Alert,
    BrokerAccount,
    BrokerOrderEvent,
    BrokerPositionSnapshot,
    BrokerSyncRun,
    CatalystEvent,
    DailyBrief,
    Filing,
    FilingSummary,
    HistoricalBar,
    Instrument,
    MacroEvent,
    MacroSeries,
    Portfolio,
    Position,
    QuoteSnapshot,
    ReconciliationException,
    ResearchNote,
    Thesis,
    TradeJournalEntry,
    Transaction,
    User,
    Watchlist,
    WatchlistItem,
    WorkspaceLayout,
)
from app.db.session import SessionLocal
from app.services.market_provider import provider_from_name


def main() -> None:
    settings = get_settings()
    provider = provider_from_name("mock")
    fixture_dir = Path(__file__).resolve().parent / "fixtures"

    instruments_payload = json.loads((fixture_dir / "instruments.json").read_text())
    quotes_payload = json.loads((fixture_dir / "quotes.json").read_text())
    brief_payload = json.loads((fixture_dir / "daily_brief.json").read_text())

    with SessionLocal() as db:
        db.execute(delete(TradeJournalEntry))
        db.execute(delete(ReconciliationException))
        db.execute(delete(BrokerOrderEvent))
        db.execute(delete(BrokerPositionSnapshot))
        db.execute(delete(BrokerSyncRun))
        db.execute(delete(BrokerAccount))
        db.execute(delete(Transaction))
        db.execute(delete(Position))
        db.execute(delete(Portfolio))
        db.execute(delete(WatchlistItem))
        db.execute(delete(Watchlist))
        db.execute(delete(QuoteSnapshot))
        db.execute(delete(HistoricalBar))
        db.execute(delete(Alert))
        db.execute(delete(FilingSummary))
        db.execute(delete(Filing))
        db.execute(delete(ResearchNote))
        db.execute(delete(Thesis))
        db.execute(delete(CatalystEvent))
        db.execute(delete(MacroEvent))
        db.execute(delete(MacroSeries))
        db.execute(delete(DailyBrief))
        db.execute(delete(WorkspaceLayout))
        db.execute(delete(Instrument))
        db.execute(delete(User))
        db.commit()

        user = User(id=settings.user_seed_id, email="local@finterm.dev", display_name="Local User")
        db.add(user)

        instruments: dict[str, Instrument] = {}
        for row in instruments_payload:
            instrument = Instrument(
                symbol=row["symbol"],
                name=row["name"],
                exchange=row["exchange"],
                asset_type=row.get("asset_type", "equity"),
                currency="USD",
                sector=row.get("sector"),
                industry=row.get("industry"),
                market_cap=Decimal(str(row["market_cap"])) if row.get("market_cap") else None,
                source_provider="mock",
            )
            db.add(instrument)
            instruments[instrument.symbol] = instrument

        db.commit()

        for instrument in instruments.values():
            db.refresh(instrument)

        now = datetime.now(UTC)

        quote_by_symbol = {row["symbol"]: row for row in quotes_payload}
        for symbol, quote in quote_by_symbol.items():
            instrument = instruments[symbol]
            db.add(
                QuoteSnapshot(
                    instrument_id=instrument.id,
                    as_of=now,
                    price=Decimal(str(quote["price"])),
                    change=Decimal(str(quote["change"])),
                    change_percent=Decimal(str(quote["change_percent"])),
                    volume=Decimal(str(quote["volume"])),
                    delay_seconds=900,
                    freshness_status="stale",
                    source_provider="mock",
                )
            )

        for symbol in ["AAPL", "MSFT", "NVDA", "SPY", "QQQ"]:
            for bar in provider.get_historical_bars(symbol=symbol, timeframe="6M", points=200):
                db.add(
                    HistoricalBar(
                        instrument_id=instruments[symbol].id,
                        timeframe="6M",
                        ts=bar.ts,
                        open=Decimal(str(bar.open)),
                        high=Decimal(str(bar.high)),
                        low=Decimal(str(bar.low)),
                        close=Decimal(str(bar.close)),
                        volume=Decimal(str(bar.volume)),
                        delay_seconds=900,
                        freshness_status="stale",
                        source_provider="mock",
                    )
                )

        core = Watchlist(user_id=user.id, name="Core", description="Primary monitoring list")
        momentum = Watchlist(user_id=user.id, name="Momentum", description="High beta names")
        db.add_all([core, momentum])
        db.commit()
        db.refresh(core)
        db.refresh(momentum)

        core_symbols = ["AAPL", "MSFT", "SPY", "QQQ"]
        momentum_symbols = ["NVDA", "META", "AMZN"]

        for index, symbol in enumerate(core_symbols):
            db.add(
                WatchlistItem(
                    watchlist_id=core.id,
                    instrument_id=instruments[symbol].id,
                    sort_order=index,
                    tags=["core", "largecap"],
                )
            )

        for index, symbol in enumerate(momentum_symbols):
            db.add(
                WatchlistItem(
                    watchlist_id=momentum.id,
                    instrument_id=instruments[symbol].id,
                    sort_order=index,
                    tags=["momentum"],
                )
            )

        portfolio = Portfolio(user_id=user.id, name="Personal", base_currency="USD")
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)

        seeded_transactions: list[tuple[str, datetime, str, Decimal, Decimal, Decimal, str]] = [
            (
                "AAPL",
                now - timedelta(days=28),
                "buy",
                Decimal("30"),
                Decimal("192.10"),
                Decimal("1.00"),
                "Initial core starter",
            ),
            (
                "AAPL",
                now - timedelta(days=8),
                "buy",
                Decimal("15"),
                Decimal("209.40"),
                Decimal("1.00"),
                "Add on pullback",
            ),
            (
                "MSFT",
                now - timedelta(days=30),
                "buy",
                Decimal("18"),
                Decimal("402.20"),
                Decimal("1.50"),
                "Cloud exposure",
            ),
            (
                "MSFT",
                now - timedelta(days=9),
                "sell",
                Decimal("4"),
                Decimal("418.80"),
                Decimal("1.25"),
                "Trim into strength",
            ),
            (
                "NVDA",
                now - timedelta(days=14),
                "buy",
                Decimal("10"),
                Decimal("841.50"),
                Decimal("1.25"),
                "AI cycle anchor",
            ),
        ]

        for symbol, trade_date, side, quantity, price, fees, notes in seeded_transactions:
            db.add(
                Transaction(
                    portfolio_id=portfolio.id,
                    instrument_id=instruments[symbol].id,
                    trade_date=trade_date,
                    side=side,
                    quantity=quantity,
                    price=price,
                    fees=fees,
                    notes=notes,
                )
            )

        macro_series = MacroSeries(
            code="US_CPI_YOY",
            name="US CPI YoY",
            description="Consumer Price Index year-over-year",
            frequency="monthly",
            source_provider="mock",
        )
        db.add(macro_series)
        db.commit()
        db.refresh(macro_series)

        for event in provider.get_macro_events():
            db.add(
                MacroEvent(
                    series_id=macro_series.id,
                    title=event.title,
                    scheduled_at=event.scheduled_at,
                    actual=event.actual,
                    forecast=event.forecast,
                    impact=event.impact,
                    country="US",
                )
            )

        filing = Filing(
            instrument_id=instruments["AAPL"].id,
            accession_no="0000320193-26-000010",
            form_type="10-Q",
            filed_at=now - timedelta(days=12),
            period_end=now - timedelta(days=20),
            filing_url="https://www.sec.gov/",
            raw_text="Seed filing text",
            source_provider="mock",
        )
        db.add(filing)
        db.commit()
        db.refresh(filing)

        db.add(
            FilingSummary(
                filing_id=filing.id,
                summary="Revenue grew modestly while services mix improved gross margin.",
                key_changes=["Services growth outpaced hardware", "R&D spend increased"],
                risks=["FX headwinds", "Supply chain concentration"],
                forward_looking=["Management cited cautious enterprise spending"],
                takeaway="Execution remains solid with tighter margin discipline.",
                model_name="seed-template",
            )
        )

        db.add_all(
            [
                ResearchNote(
                    user_id=user.id,
                    instrument_id=instruments["AAPL"].id,
                    title="AAPL position review",
                    content="Tracking service attach and buyback cadence.",
                    note_type="thesis",
                    theme="Quality compounders",
                    sector="Technology",
                ),
                ResearchNote(
                    user_id=user.id,
                    instrument_id=instruments["AAPL"].id,
                    title="Risk update",
                    content="Valuation rich into CPI week.",
                    note_type="risk",
                    theme="Macro sensitivity",
                    sector="Technology",
                ),
                ResearchNote(
                    user_id=user.id,
                    instrument_id=instruments["AAPL"].id,
                    title="Catalyst prep",
                    content="Watch iPhone cycle commentary and monitor China demand tone.",
                    note_type="catalyst",
                    theme="Product cycle",
                    sector="Technology",
                ),
            ]
        )

        db.add_all(
            [
                Thesis(
                    user_id=user.id,
                    instrument_id=instruments["AAPL"].id,
                    title="AAPL Core Thesis",
                    status="active",
                    summary=(
                        "Services mix expansion and capital return support steady compounding, "
                        "with near-term volatility tied to macro demand signals."
                    ),
                ),
                Thesis(
                    user_id=user.id,
                    instrument_id=instruments["NVDA"].id,
                    title="NVDA Tactical Thesis",
                    status="watch",
                    summary="AI capex cycle remains strong; monitor valuation and supply constraints.",
                ),
            ]
        )

        db.add_all(
            [
                CatalystEvent(
                    user_id=user.id,
                    instrument_id=instruments["AAPL"].id,
                    title="Product launch event",
                    event_date=now + timedelta(days=25),
                    status="upcoming",
                    notes="Monitor guidance language.",
                ),
                CatalystEvent(
                    user_id=user.id,
                    instrument_id=instruments["AAPL"].id,
                    title="Next earnings",
                    event_date=now + timedelta(days=48),
                    status="scheduled",
                    notes="Check services growth and buyback pace.",
                ),
            ]
        )

        for symbol in ["AAPL", "NVDA", "SPY"]:
            db.add(
                Alert(
                    user_id=user.id,
                    instrument_id=instruments[symbol].id,
                    alert_type="price_threshold",
                    rule={"operator": ">=", "target": quote_by_symbol[symbol]["price"] * 1.02},
                    status="active",
                    next_eval_at=now + timedelta(minutes=5),
                    source_provider="mock",
                )
            )

        db.add(
            DailyBrief(
                user_id=user.id,
                headline=brief_payload["headline"],
                bullets=brief_payload["bullets"],
                body="Seeded morning brief.",
                generated_at=now,
                source_model="seed-template",
            )
        )

        db.add(
            WorkspaceLayout(
                user_id=user.id,
                workspace="watchlists",
                state={"sortBy": "symbol", "sortDirection": "asc", "filterTag": None},
            )
        )

        db.commit()

        watchlist_count = db.execute(select(Watchlist)).scalars().all()
        print(f"Seed complete. Watchlists: {len(watchlist_count)}")


if __name__ == "__main__":
    main()
