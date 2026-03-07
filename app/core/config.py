from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "local"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    database_url: str = "postgresql+psycopg://postgres:postgres@db:5432/sota_ingestion"
    redis_url: str = "redis://redis:6379/0"

    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/2"

    default_connector_mode: str = "mock"
    bsale_base_url: str = "http://mock-bsale-api:8010/v1"
    bsale_api_token: str = "mock-token"


@lru_cache
def get_settings() -> Settings:
    return Settings()
