from functools import lru_cache

from fastapi import Header

from app.core.config import get_settings
from app.services.cache import CacheService
from app.services.market_provider import MarketDataProvider, provider_from_name


@lru_cache(maxsize=1)
def get_provider() -> MarketDataProvider:
    settings = get_settings()
    return provider_from_name(settings.market_data_provider)


@lru_cache(maxsize=1)
def get_cache() -> CacheService:
    return CacheService()


def get_user_id(x_user_id: str | None = Header(default=None)) -> str:
    settings = get_settings()
    return x_user_id or settings.user_seed_id
