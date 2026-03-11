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
    filings_provider: str = Field(default="mock_sec", alias="FILINGS_PROVIDER")
    macro_provider: str = Field(default="mock_macro", alias="MACRO_PROVIDER")
    user_seed_id: str = Field(default="00000000-0000-0000-0000-000000000001", alias="USER_SEED_ID")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
