from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "finterm-api"
    api_prefix: str = "/api/v1"
    debug: bool = False

    database_url: str = Field(
        default="postgresql+psycopg://localhost:5432/finterm",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    market_data_provider: str = Field(default="mock", alias="MARKET_DATA_PROVIDER")
    alpha_vantage_api_key: str = Field(default="", alias="ALPHA_VANTAGE_API_KEY")
    alpha_vantage_base_url: str = Field(
        default="https://www.alphavantage.co/query",
        alias="ALPHA_VANTAGE_BASE_URL",
    )
    filings_provider: str = Field(default="mock_sec", alias="FILINGS_PROVIDER")
    macro_provider: str = Field(default="mock_macro", alias="MACRO_PROVIDER")
    broker_provider: str = Field(default="mock_broker", alias="BROKER_PROVIDER")
    broker_trading_enabled: bool = Field(default=False, alias="BROKER_TRADING_ENABLED")
    retrieval_provider: str = Field(default="mock_embed", alias="RETRIEVAL_PROVIDER")
    user_seed_id: str = Field(default="00000000-0000-0000-0000-000000000001", alias="USER_SEED_ID")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
