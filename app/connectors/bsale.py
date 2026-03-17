from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import replace
from typing import Any
from urllib.parse import urlparse

import httpx

from app.core.config import get_settings
from app.core.utils import clean_string

from .base import BaseConnector, ConnectorConfig, ConnectorConfigurationError, ConnectorMode

logger = logging.getLogger(__name__)

DEFAULT_MOCK_BASE_URL = "http://mock-bsale-api:8010/v1"
DEFAULT_REAL_BASE_URL = "https://api.bsale.io/v1"
DEFAULT_MOCK_API_TOKEN = "mock-token"


class BsaleConnector(BaseConnector):
    def __init__(self, base_url: str, token: str, timeout_s: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.headers = {"access_token": token}
        self.timeout_s = timeout_s

    async def _fetch_json(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> Any:
        async def _request(active_client: httpx.AsyncClient) -> Any:
            response = await active_client.get(f"{self.base_url}/{endpoint}", headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()

        if client is not None:
            return await _request(client)

        async with httpx.AsyncClient(timeout=self.timeout_s) as active_client:
            return await _request(active_client)

    async def _fetch_items(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> list[dict[str, Any]]:
        payload = await self._fetch_json(endpoint, params=params, client=client)
        if isinstance(payload, dict) and "items" in payload:
            return payload["items"]
        return payload

    async def _fetch_paginated(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        *,
        page_size: int = 50,
        client: httpx.AsyncClient | None = None,
    ) -> list[dict[str, Any]]:
        collected: list[dict[str, Any]] = []
        offset = 0
        t0 = time.monotonic()
        while True:
            page_params = dict(params or {})
            page_params.update({"limit": str(page_size), "offset": str(offset)})
            items = await self._fetch_items(endpoint, params=page_params, client=client)
            if not items:
                break
            collected.extend(items)
            if len(items) < page_size:
                break
            offset += len(items)
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        logger.info("fetched %d records from %s in %dms", len(collected), endpoint, elapsed_ms)
        return collected

    @staticmethod
    def _endpoint_from_href(href: str | None) -> str | None:
        if not href:
            return None
        path = urlparse(href).path or href
        if "/v1/" in path:
            return path.split("/v1/", 1)[1].lstrip("/")
        return path.lstrip("/")

    async def _ensure_detail_items(
        self,
        records: list[dict[str, Any]],
        *,
        client: httpx.AsyncClient,
    ) -> list[dict[str, Any]]:
        enriched: list[dict[str, Any]] = []
        for record in records:
            details = record.get("details")
            if isinstance(details, dict) and details.get("items") is not None:
                enriched.append(record)
                continue

            endpoint = None
            if isinstance(details, dict):
                endpoint = self._endpoint_from_href(details.get("href"))
            elif isinstance(details, str):
                endpoint = self._endpoint_from_href(details)

            if not endpoint:
                enriched.append(record)
                continue

            detail_items = await self._fetch_items(endpoint, client=client)
            enriched.append(
                {
                    **record,
                    "details": {
                        **(details if isinstance(details, dict) else {}),
                        "items": detail_items,
                        "count": len(detail_items),
                    },
                }
            )
        return enriched

    async def fetch_products(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self.timeout_s) as client:
            products = await self._fetch_paginated("products.json", client=client)
            enriched_products: list[dict[str, Any]] = []
            for product in products:
                product_id = product.get("id")
                if product_id is None:
                    enriched_products.append(product)
                    continue
                variants, product_taxes = await asyncio.gather(
                    self._fetch_paginated(f"products/{product_id}/variants.json", client=client),
                    self._fetch_paginated(f"products/{product_id}/product_taxes.json", client=client),
                )
                enriched_products.append(
                    {
                        **product,
                        "variants": variants,
                        "product_taxes_items": product_taxes,
                    }
                )
            return enriched_products

    async def fetch_clients(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self.timeout_s) as client:
            clients = await self._fetch_paginated("clients.json", client=client)
            enriched_clients: list[dict[str, Any]] = []
            for client_payload in clients:
                client_id = client_payload.get("id")
                if client_id is None:
                    enriched_clients.append(client_payload)
                    continue
                client_detail, contacts, addresses, attributes = await asyncio.gather(
                    self._fetch_json(f"clients/{client_id}.json", client=client),
                    self._fetch_paginated(f"clients/{client_id}/contacts.json", client=client),
                    self._fetch_paginated(f"clients/{client_id}/addresses.json", client=client),
                    self._fetch_paginated(f"clients/{client_id}/attributes.json", client=client),
                )
                enriched_clients.append(
                    {
                        **client_payload,
                        **client_detail,
                        "contacts_items": contacts,
                        "addresses_items": addresses,
                        "attributes_items": attributes,
                    }
                )
            return enriched_clients

    async def fetch_stock(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self.timeout_s) as client:
            snapshot, receptions, consumptions = await asyncio.gather(
                self._fetch_paginated("stocks.json", client=client),
                self._fetch_paginated("stocks/receptions.json", params={"expand": "details"}, client=client),
                self._fetch_paginated("stocks/consumptions.json", params={"expand": "details"}, client=client),
            )
            receptions, consumptions = await asyncio.gather(
                self._ensure_detail_items(receptions, client=client),
                self._ensure_detail_items(consumptions, client=client),
            )
        return [
            *[{**record, "_stock_record_type": "snapshot", "_source_endpoint": "stocks.json"} for record in snapshot],
            *[
                {**record, "_stock_record_type": "reception", "_source_endpoint": "stocks/receptions.json"}
                for record in receptions
            ],
            *[
                {**record, "_stock_record_type": "consumption", "_source_endpoint": "stocks/consumptions.json"}
                for record in consumptions
            ],
        ]

    async def fetch_stock_receptions(self) -> list[dict[str, Any]]:
        return await self._fetch_paginated("stocks/receptions.json", params={"expand": "details"})

    async def fetch_stock_consumptions(self) -> list[dict[str, Any]]:
        return await self._fetch_paginated("stocks/consumptions.json", params={"expand": "details"})

    async def fetch_sales_documents(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self.timeout_s) as client:
            documents = await self._fetch_paginated("documents.json", params={"expand": "details", "state": "0"}, client=client)
            if not documents:
                documents = await self._fetch_paginated("documents.json", params={"expand": "details"}, client=client)
            return await self._ensure_detail_items(documents, client=client)

    async def fetch_branches(self) -> list[dict[str, Any]]:
        return await self._fetch_paginated("offices.json")

    async def fetch_document_types(self) -> list[dict[str, Any]]:
        return await self._fetch_paginated("document_types.json")


_clean = clean_string


def _normalize_base_url(value: str | None) -> str | None:
    candidate = _clean(value)
    return candidate.rstrip("/") if candidate else None


def _sanitize_real_base_url(value: str | None) -> str | None:
    candidate = _normalize_base_url(value)
    if not candidate:
        return None

    lowered = candidate.lower()
    if lowered in {"https://api.bsale.cl", "http://api.bsale.cl", "https://api.bsale.cl/v1", "http://api.bsale.cl/v1"}:
        return DEFAULT_REAL_BASE_URL
    if lowered in {"https://api.bsale.io", "http://api.bsale.io"}:
        return DEFAULT_REAL_BASE_URL

    if lowered.startswith("https://api.bsale.cl/") or lowered.startswith("http://api.bsale.cl/"):
        suffix = candidate.split("api.bsale.cl", 1)[1]
        candidate = "https://api.bsale.io" + suffix
        lowered = candidate.lower()

    if lowered.startswith("https://api.bsale.io/") or lowered.startswith("http://api.bsale.io/"):
        if lowered == "https://api.bsale.io/v1" or lowered == "http://api.bsale.io/v1":
            return DEFAULT_REAL_BASE_URL
        if "/v1/" not in lowered and not lowered.endswith("/v1"):
            return candidate + "/v1"

    return candidate


def normalize_bsale_base_url(*, mode: ConnectorMode, value: str | None) -> str | None:
    if mode == ConnectorMode.MOCK:
        return _normalize_base_url(value)
    return _sanitize_real_base_url(value)



def _looks_like_mock_url(value: str | None) -> bool:
    candidate = _normalize_base_url(value)
    return bool(candidate) and "mock-bsale-api" in candidate



def _is_mock_token(value: str | None) -> bool:
    return _clean(value) == DEFAULT_MOCK_API_TOKEN



def resolve_mock_base_url() -> str:
    settings = get_settings()
    configured = _normalize_base_url(getattr(settings, "bsale_mock_base_url", None))
    if configured:
        return configured

    legacy = _normalize_base_url(settings.bsale_base_url)
    if _looks_like_mock_url(legacy):
        return legacy  # backward compatibility with older .env files

    return DEFAULT_MOCK_BASE_URL



def resolve_real_base_url() -> str:
    settings = get_settings()
    configured = _sanitize_real_base_url(settings.bsale_base_url)
    if configured and not _looks_like_mock_url(configured):
        return configured
    return DEFAULT_REAL_BASE_URL



def resolve_real_api_key() -> str | None:
    settings = get_settings()
    for candidate in (getattr(settings, "bsale_api_key", None), settings.bsale_api_token):
        normalized = _clean(candidate)
        if normalized and not _is_mock_token(normalized):
            return normalized
    return None



def build_bsale_config(
    *,
    mode: ConnectorMode,
    base_url: str | None = None,
    api_key: str | None = None,
    current: ConnectorConfig | None = None,
) -> ConnectorConfig:
    current = current or ConnectorConfig(name="bsale", mode=ConnectorMode.MOCK, base_url=resolve_mock_base_url())

    if mode == ConnectorMode.MOCK:
        return replace(
            current,
            name="bsale",
            mode=ConnectorMode.MOCK,
            base_url=normalize_bsale_base_url(mode=ConnectorMode.MOCK, value=base_url) or resolve_mock_base_url(),
            api_key=None,
        )

    current_base_url = normalize_bsale_base_url(mode=ConnectorMode.REAL, value=current.base_url)
    current_api_key = _clean(current.api_key)
    if _is_mock_token(current_api_key):
        current_api_key = None

    candidate = replace(
        current,
        name="bsale",
        mode=ConnectorMode.REAL,
        base_url=normalize_bsale_base_url(mode=ConnectorMode.REAL, value=base_url) or current_base_url or resolve_real_base_url(),
        api_key=_clean(api_key) or current_api_key or resolve_real_api_key(),
    )

    missing: list[str] = []
    if not candidate.base_url:
        missing.append("base_url")
    if not candidate.api_key:
        missing.append("api_key")
    if missing:
        raise ConnectorConfigurationError(
            "Falta configuracion para modo real de Bsale: " + ", ".join(missing)
        )

    return candidate



def probe_bsale_connection(
    config: ConnectorConfig,
    timeout_s: float = 3.0,
) -> tuple[bool, str, dict[str, Any] | None]:
    if config.mode == ConnectorMode.MOCK:
        return True, "Modo mock habilitado; no se valida conectividad real.", None

    if not config.api_key:
        raise ConnectorConfigurationError("Falta configuracion para modo real de Bsale: api_key")

    base_url = config.base_url.rstrip("/")
    headers = {"access_token": config.api_key}

    try:
        with httpx.Client(timeout=timeout_s, follow_redirects=True) as client:
            products_url = base_url + "/products.json"
            products_response = client.get(products_url, headers=headers, params={"limit": 1, "offset": 0})
            if products_response.is_success:
                try:
                    payload = products_response.json()
                except ValueError:
                    payload = None
                try:
                    clients_url = base_url + "/clients.json"
                    clients_response = client.get(clients_url, headers=headers, params={"limit": 1, "offset": 0})
                except httpx.HTTPError as exc:
                    return False, f"Lectura OK de products.json en {products_url}, pero fallo lectura de clientes: {exc}", payload
                if not clients_response.is_success:
                    detail = " ".join(clients_response.text.split())[:200] or "sin detalle"
                    return False, (
                        f"Lectura OK de products.json en {products_url}, pero clients.json respondio HTTP {clients_response.status_code}: {detail}"
                    ), payload
                return True, f"Conexion exitosa a {base_url}; lectura OK de products.json y clients.json.", payload
    except httpx.HTTPError as exc:
        return False, f"No fue posible conectar a Bsale ({products_url}): {exc}", None

    detail = " ".join(products_response.text.split())[:200] or "sin detalle"
    return False, f"Bsale respondio HTTP {products_response.status_code} al consultar {products_url}: {detail}", None


def attempt_bsale_connection(config: ConnectorConfig, timeout_s: float = 3.0) -> tuple[bool, str]:
    connected, message, _ = probe_bsale_connection(config, timeout_s=timeout_s)
    return connected, message



def build_bsale_job_connector(*, mode: str | ConnectorMode, base_url: str, api_key: str | None) -> BsaleConnector:
    connector_mode = mode if isinstance(mode, ConnectorMode) else ConnectorMode(mode)

    if connector_mode == ConnectorMode.MOCK:
        normalized_base_url = normalize_bsale_base_url(mode=ConnectorMode.MOCK, value=base_url) or resolve_mock_base_url()
        return BsaleConnector(base_url=normalized_base_url.rstrip("/"), token=DEFAULT_MOCK_API_TOKEN)

    normalized_api_key = _clean(api_key)
    if not normalized_api_key:
        raise ConnectorConfigurationError("Falta configuracion para modo real de Bsale: api_key")

    normalized_base_url = normalize_bsale_base_url(mode=ConnectorMode.REAL, value=base_url) or resolve_real_base_url()
    return BsaleConnector(base_url=normalized_base_url.rstrip("/"), token=normalized_api_key)


class BsaleConnectorState:
    def __init__(self) -> None:
        self._config = build_bsale_config(mode=ConnectorMode.MOCK)

    @property
    def config(self) -> ConnectorConfig:
        return self._config

    def reset(self) -> ConnectorConfig:
        self._config = build_bsale_config(mode=ConnectorMode.MOCK)
        return self._config

    def update(self, *, mode: ConnectorMode, base_url: str | None = None, api_key: str | None = None) -> ConnectorConfig:
        self._config = build_bsale_config(mode=mode, base_url=base_url, api_key=api_key, current=self._config)
        return self._config

    def attempt_connection(self, timeout_s: float = 3.0) -> tuple[bool, str]:
        return attempt_bsale_connection(self._config, timeout_s=timeout_s)


bsale_connector = BsaleConnectorState()
