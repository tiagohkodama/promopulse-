from functools import lru_cache
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    app_name: str = "PromoPulse API"
    environment: str = "development"
    version: str = "0.1.0"
    log_level: str = "INFO"

    # Placeholder for later DB usage
    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/promopulse"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> AppSettings:
    """
    Returns a cached instance of AppSettings.
    Using lru_cache ensures we only load and parse env vars once.
    """
    return AppSettings()
