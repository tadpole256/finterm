from functools import lru_cache

from fastapi import Header

from app.core.config import get_settings
from app.services.broker_provider import BrokerProvider, broker_provider_from_name
from app.services.cache import CacheService
from app.services.filings_provider import FilingsProvider, filings_provider_from_name
from app.services.macro_provider import MacroProvider, macro_provider_from_name
from app.services.market_provider import MarketDataProvider, provider_from_name


@lru_cache(maxsize=1)
def get_provider() -> MarketDataProvider:
    settings = get_settings()
    return provider_from_name(settings.market_data_provider)


@lru_cache(maxsize=1)
def get_cache() -> CacheService:
    return CacheService()


@lru_cache(maxsize=1)
def get_filings_provider() -> FilingsProvider:
    settings = get_settings()
    return filings_provider_from_name(settings.filings_provider)


@lru_cache(maxsize=1)
def get_macro_provider() -> MacroProvider:
    settings = get_settings()
    return macro_provider_from_name(settings.macro_provider)


@lru_cache(maxsize=1)
def get_broker_provider() -> BrokerProvider:
    settings = get_settings()
    return broker_provider_from_name(settings.broker_provider)


def get_user_id(x_user_id: str | None = Header(default=None)) -> str:
    settings = get_settings()
    return x_user_id or settings.user_seed_id
