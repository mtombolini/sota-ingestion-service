from __future__ import annotations

import asyncio
from dataclasses import replace
from typing import Any

import httpx

from app.core.config import get_settings

from .base import BaseConnector, ConnectorConfig, ConnectorConfigurationError, ConnectorMode

DEFAULT_MOCK_BASE_URL = "http://mock-bsale-api:8010/v1"
DEFAULT_REAL_BASE_URL = "https://api.bsale.cl/v1"
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
        return collected

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
        return await self._fetch_paginated("stocks.json")

    async def fetch_sales_documents(self) -> list[dict[str, Any]]:
        return await self._fetch_paginated("documents.json", params={"expand": "details", "state": "0"})

    async def fetch_branches(self) -> list[dict[str, Any]]:
        return await self._fetch_paginated("offices.json")

    async def fetch_document_types(self) -> list[dict[str, Any]]:
        return await self._fetch_paginated("document_types.json")


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    candidate = value.strip()
    return candidate or None



def _normalize_base_url(value: str | None) -> str | None:
    candidate = _clean(value)
    return candidate.rstrip("/") if candidate else None



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
    configured = _normalize_base_url(settings.bsale_base_url)
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
            base_url=_normalize_base_url(base_url) or resolve_mock_base_url(),
            api_key=None,
        )

    current_base_url = _normalize_base_url(current.base_url)
    current_api_key = _clean(current.api_key)
    if _is_mock_token(current_api_key):
        current_api_key = None

    candidate = replace(
        current,
        name="bsale",
        mode=ConnectorMode.REAL,
        base_url=_normalize_base_url(base_url) or current_base_url or resolve_real_base_url(),
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
    url = base_url + "/company.json"
    headers = {"access_token": config.api_key}

    try:
        with httpx.Client(timeout=timeout_s, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            if response.is_success:
                try:
                    payload = response.json()
                except ValueError:
                    payload = None
                try:
                    products_response = client.get(base_url + "/products.json", headers=headers, params={"limit": 1, "offset": 0})
                except httpx.HTTPError as exc:
                    return False, f"Conexion base OK en {url}, pero fallo lectura de productos: {exc}", payload
                if not products_response.is_success:
                    detail = " ".join(products_response.text.split())[:200] or "sin detalle"
                    return False, (
                        f"Conexion base OK en {url}, pero products.json respondio HTTP {products_response.status_code}: {detail}"
                    ), payload
                try:
                    clients_response = client.get(base_url + "/clients.json", headers=headers, params={"limit": 1, "offset": 0})
                except httpx.HTTPError as exc:
                    return False, f"Conexion base OK en {url}, pero fallo lectura de clientes: {exc}", payload
                if not clients_response.is_success:
                    detail = " ".join(clients_response.text.split())[:200] or "sin detalle"
                    return False, (
                        f"Conexion base OK en {url}, pero clients.json respondio HTTP {clients_response.status_code}: {detail}"
                    ), payload
                return True, f"Conexion exitosa a {url} y lectura OK de products.json y clients.json.", payload
    except httpx.HTTPError as exc:
        return False, f"No fue posible conectar a Bsale ({url}): {exc}", None

    detail = " ".join(response.text.split())[:200] or "sin detalle"
    return False, f"Bsale respondio HTTP {response.status_code} al consultar {url}: {detail}", None


def attempt_bsale_connection(config: ConnectorConfig, timeout_s: float = 3.0) -> tuple[bool, str]:
    connected, message, _ = probe_bsale_connection(config, timeout_s=timeout_s)
    return connected, message



def build_bsale_job_connector(*, mode: str | ConnectorMode, base_url: str, api_key: str | None) -> BsaleConnector:
    connector_mode = mode if isinstance(mode, ConnectorMode) else ConnectorMode(mode)

    if connector_mode == ConnectorMode.MOCK:
        return BsaleConnector(base_url=base_url.rstrip("/"), token=DEFAULT_MOCK_API_TOKEN)

    normalized_api_key = _clean(api_key)
    if not normalized_api_key:
        raise ConnectorConfigurationError("Falta configuracion para modo real de Bsale: api_key")

    return BsaleConnector(base_url=base_url.rstrip("/"), token=normalized_api_key)


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
