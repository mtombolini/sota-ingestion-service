import httpx
from typing import Any

from app.connectors.base import BaseConnector


class BsaleConnector(BaseConnector):
    def __init__(self, base_url: str, token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.headers = {"access_token": token}

    async def _fetch(self, endpoint: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(f"{self.base_url}/{endpoint}", headers=self.headers, params=params)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, dict) and "items" in data:
                return data["items"]
            return data

    async def fetch_products(self) -> list[dict[str, Any]]:
        return await self._fetch("products.json")

    async def fetch_stock(self) -> list[dict[str, Any]]:
        return await self._fetch("stocks.json")

    async def fetch_sales_documents(self) -> list[dict[str, Any]]:
        return await self._fetch("documents/sales.json")

    async def fetch_branches(self) -> list[dict[str, Any]]:
        return await self._fetch("offices.json")
