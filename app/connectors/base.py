from abc import ABC, abstractmethod
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
