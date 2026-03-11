from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import (
    get_cache,
    get_filings_provider,
    get_macro_provider,
    get_provider,
    get_user_id,
)
from app.db.base import Base
from app.db.models import (
    Alert,
    CatalystEvent,
    DailyBrief,
    Filing,
    FilingSummary,
    Instrument,
    Portfolio,
    ResearchNote,
    Thesis,
    Transaction,
    User,
    Watchlist,
    WatchlistItem,
    WorkspaceLayout,
)
from app.db.session import get_db
from app.main import app
from app.services.cache import CacheService
from app.services.filings_provider import MockSecFilingsProvider
from app.services.macro_provider import MockMacroProvider
from app.services.market_provider import MockMarketDataProvider


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        seed_test_data(session)
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_provider] = lambda: MockMarketDataProvider()
    app.dependency_overrides[get_filings_provider] = lambda: MockSecFilingsProvider()
    app.dependency_overrides[get_macro_provider] = lambda: MockMacroProvider()
    app.dependency_overrides[get_cache] = lambda: CacheService()
    app.dependency_overrides[get_user_id] = lambda: "00000000-0000-0000-0000-000000000001"

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def seed_test_data(session: Session) -> None:
    user = User(id="00000000-0000-0000-0000-000000000001", email="test@local", display_name="Test")
    session.add(user)

    instruments = [
        Instrument(
            id="ins-aapl",
            symbol="AAPL",
            name="Apple Inc.",
            exchange="NASDAQ",
            asset_type="equity",
            currency="USD",
            sector="Technology",
            industry="Consumer Electronics",
            market_cap=Decimal("2965000000000"),
            source_provider="mock",
        ),
        Instrument(
            id="ins-msft",
            symbol="MSFT",
            name="Microsoft Corporation",
            exchange="NASDAQ",
            asset_type="equity",
            currency="USD",
            sector="Technology",
            industry="Software",
            market_cap=Decimal("3128000000000"),
            source_provider="mock",
        ),
        Instrument(
            id="ins-nvda",
            symbol="NVDA",
            name="NVIDIA Corporation",
            exchange="NASDAQ",
            asset_type="equity",
            currency="USD",
            sector="Technology",
            industry="Semiconductors",
            market_cap=Decimal("2280000000000"),
            source_provider="mock",
        ),
    ]
    session.add_all(instruments)

    watchlist = Watchlist(id="watchlist-core", user_id=user.id, name="Core", description="Main")
    session.add(watchlist)
    session.flush()

    session.add_all(
        [
            WatchlistItem(
                id="item-aapl",
                watchlist_id=watchlist.id,
                instrument_id="ins-aapl",
                sort_order=0,
                tags=["core"],
            ),
            WatchlistItem(
                id="item-msft",
                watchlist_id=watchlist.id,
                instrument_id="ins-msft",
                sort_order=1,
                tags=["core", "software"],
            ),
        ]
    )

    session.add(
        Alert(
            id="alert-aapl",
            user_id=user.id,
            instrument_id="ins-aapl",
            alert_type="price_threshold",
            rule={"operator": ">=", "target": 220},
            status="active",
            next_eval_at=datetime.now(UTC) + timedelta(minutes=5),
            source_provider="mock",
        )
    )

    filing = Filing(
        id="filing-aapl",
        instrument_id="ins-aapl",
        accession_no="0000",
        form_type="10-Q",
        filed_at=datetime.now(UTC) - timedelta(days=3),
        period_end=datetime.now(UTC) - timedelta(days=10),
        filing_url="https://www.sec.gov/",
        raw_text="Test",
        source_provider="mock",
    )
    session.add(filing)
    session.flush()

    session.add(
        FilingSummary(
            filing_id=filing.id,
            summary="Margin expansion remained stable.",
            key_changes=["services"],
            risks=["fx"],
            forward_looking=["guidance"],
            takeaway="Stable",
            model_name="seed",
        )
    )

    session.add(
        ResearchNote(
            id="note-aapl",
            user_id=user.id,
            instrument_id="ins-aapl",
            title="AAPL note",
            content="Track gross margin",
            note_type="thesis",
            theme="quality",
            sector="Technology",
        )
    )
    session.add(
        ResearchNote(
            id="note-aapl-risk",
            user_id=user.id,
            instrument_id="ins-aapl",
            title="AAPL risk update",
            content="Risk: demand softness in EMEA. Watch channel inventory normalization.",
            note_type="risk",
            theme="quality",
            sector="Technology",
        )
    )
    session.add(
        Thesis(
            id="thesis-aapl",
            user_id=user.id,
            instrument_id="ins-aapl",
            title="AAPL thesis",
            status="active",
            summary="Services expansion offsets hardware cyclicality.",
        )
    )

    session.add(
        CatalystEvent(
            id="cat-aapl",
            user_id=user.id,
            instrument_id="ins-aapl",
            title="Earnings",
            event_date=datetime.now(UTC) + timedelta(days=10),
            status="upcoming",
            notes="Watch guidance",
        )
    )

    session.add(
        DailyBrief(
            id="brief-1",
            user_id=user.id,
            headline="Test brief",
            bullets=["Point 1", "Point 2"],
            body="Body",
            generated_at=datetime.now(UTC),
            source_model="seed",
        )
    )

    session.add(
        WorkspaceLayout(
            id="layout-watchlists",
            user_id=user.id,
            workspace="watchlists",
            state={"sortBy": "symbol", "sortDirection": "asc", "filterTag": None},
        )
    )

    portfolio = Portfolio(
        id="portfolio-main",
        user_id=user.id,
        name="Personal",
        base_currency="USD",
    )
    session.add(portfolio)

    session.add_all(
        [
            Transaction(
                id="txn-aapl-buy",
                portfolio_id=portfolio.id,
                instrument_id="ins-aapl",
                trade_date=datetime.now(UTC) - timedelta(days=14),
                side="buy",
                quantity=Decimal("20"),
                price=Decimal("198.50"),
                fees=Decimal("1.00"),
                notes="Starter",
            ),
            Transaction(
                id="txn-aapl-add",
                portfolio_id=portfolio.id,
                instrument_id="ins-aapl",
                trade_date=datetime.now(UTC) - timedelta(days=5),
                side="buy",
                quantity=Decimal("10"),
                price=Decimal("208.00"),
                fees=Decimal("1.00"),
                notes="Add",
            ),
            Transaction(
                id="txn-msft-buy",
                portfolio_id=portfolio.id,
                instrument_id="ins-msft",
                trade_date=datetime.now(UTC) - timedelta(days=10),
                side="buy",
                quantity=Decimal("12"),
                price=Decimal("411.75"),
                fees=Decimal("1.00"),
                notes="Core",
            ),
            Transaction(
                id="txn-msft-sell",
                portfolio_id=portfolio.id,
                instrument_id="ins-msft",
                trade_date=datetime.now(UTC) - timedelta(days=2),
                side="sell",
                quantity=Decimal("2"),
                price=Decimal("426.20"),
                fees=Decimal("1.00"),
                notes="Trim",
            ),
        ]
    )

    session.commit()
