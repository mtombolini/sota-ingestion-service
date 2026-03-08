from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class BaseConnector(ABC):
    @abstractmethod
    async def fetch_products(self) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def fetch_stock(self) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def fetch_sales_documents(self) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def fetch_branches(self) -> list[dict[str, Any]]: ...


class ConnectorMode(str, Enum):
    MOCK = "mock"
    REAL = "real"


class ConnectionStatus(str, Enum):
    MOCK = "mock"
    CONFIG_INCOMPLETE = "config_incomplete"
    CONFIGURED = "configured"
    HEALTHY = "healthy"
    AUTH_FAILED = "auth_failed"
    CONNECTION_ERROR = "connection_error"


@dataclass
class ConnectorConfig:
    name: str
    mode: ConnectorMode = ConnectorMode.MOCK
    base_url: str = ""
    api_key: str | None = None
    extras: dict[str, Any] = field(default_factory=dict)

    def masked_api_key(self) -> str | None:
        if not self.api_key:
            return None
        visible = self.api_key[-4:] if len(self.api_key) >= 4 else self.api_key
        return f"***{visible}"


class ConnectorConfigurationError(ValueError):
    """Raised when a connector does not have enough information to run in real mode."""
