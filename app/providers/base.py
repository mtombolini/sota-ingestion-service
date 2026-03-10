from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.connectors.base import BaseConnector, ConnectorMode
from app.models import IntegrationConnection
from app.secrets import SecretStore


@dataclass(frozen=True)
class ProviderJobDefinition:
    job_type: str
    label: str
    description: str


@dataclass(frozen=True)
class ProviderCheckResult:
    connected: bool
    message: str
    provider_account_id: str | None = None
    checked_at: datetime | None = None


class ProviderDefinition(ABC):
    key: str
    display_name: str
    description: str
    environments: tuple[str, ...]
    default_environment: str
    docs_url: str | None = None

    @property
    @abstractmethod
    def jobs(self) -> tuple[ProviderJobDefinition, ...]: ...

    @abstractmethod
    def default_connection_name(self, *, ordinal: int) -> str: ...

    @abstractmethod
    def default_base_url(self, *, mode: ConnectorMode) -> str: ...

    @abstractmethod
    def apply_configuration(
        self,
        db: Session,
        conn: IntegrationConnection,
        payload: dict[str, Any],
        *,
        secret_store: SecretStore,
    ) -> str: ...

    @abstractmethod
    def check_connection(
        self,
        db: Session,
        conn: IntegrationConnection,
        *,
        secret_store: SecretStore,
    ) -> ProviderCheckResult: ...

    @abstractmethod
    def build_runtime_connector(
        self,
        db: Session,
        conn: IntegrationConnection,
        *,
        secret_store: SecretStore,
    ) -> BaseConnector: ...

    @abstractmethod
    def normalize(self, job_type: str, payload: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def source_endpoint_for_job(self, job_type: str) -> str: ...

    def source_system(self) -> str:
        return self.key

    def supports_job(self, job_type: str) -> bool:
        return any(job.job_type == job_type for job in self.jobs)

    async def fetch_records(self, connector: BaseConnector, job_type: str) -> list[dict[str, Any]]:
        if job_type == "sync_product_catalog":
            return await connector.fetch_products()
        if job_type == "sync_locations":
            return await connector.fetch_branches()
        if job_type == "sync_stock":
            return await connector.fetch_stock()
        if job_type == "sync_sales_orders":
            return await connector.fetch_sales_documents()
        if job_type == "sync_customers":
            return await connector.fetch_clients()
        if job_type == "sync_document_types":
            return await connector.fetch_document_types()
        raise ValueError(f"unsupported job type {job_type}")
