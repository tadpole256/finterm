from sqlalchemy.orm import Session

from app.services.market_provider import MockMarketDataProvider
from app.services.screening import ScreenerFilters, ScreenerService


def test_screener_filters_by_price_and_sector(db_session: Session) -> None:
    service = ScreenerService(db_session, MockMarketDataProvider())

    results = service.run(
        ScreenerFilters(
            price_min=200,
            price_max=900,
            sector="Technology",
        )
    )

    symbols = {row["symbol"] for row in results}
    assert "AAPL" in symbols
    assert "MSFT" in symbols
