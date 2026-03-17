import logging
from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

_INSECURE_DEFAULT_KEY = "dev-secret-store-key-change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "local"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    database_url: str = "postgresql+psycopg://postgres:postgres@db:5432/sota_ingestion"
    redis_url: str = "redis://redis:6379/0"

    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/2"

    # Database connection pool
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_recycle: int = 1800

    default_connector_mode: str = "mock"
    bsale_mock_base_url: str = "http://mock-bsale-api:8010/v1"
    bsale_base_url: str = "https://api.bsale.io/v1"
    bsale_api_token: str | None = None
    bsale_api_key: str | None = None
    secret_store_key: str = _INSECURE_DEFAULT_KEY
    cors_origins: str | None = None

    @model_validator(mode="after")
    def _validate_production_settings(self):
        if self.app_env == "production":
            if self.secret_store_key == _INSECURE_DEFAULT_KEY:
                raise ValueError(
                    "SECRET_STORE_KEY must be set to a secure value in production. "
                    "Do not use the default dev key."
                )
            if "postgres:postgres@" in self.database_url:
                logger.warning("Production is using default database credentials — consider changing DATABASE_URL.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
