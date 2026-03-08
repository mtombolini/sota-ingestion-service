from __future__ import annotations

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

    async def _fetch(self, endpoint: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self.timeout_s) as client:
            response = await client.get(f"{self.base_url}/{endpoint}", headers=self.headers, params=params)
            response.raise_for_status()
            payload = response.json()
            if isinstance(payload, dict) and "items" in payload:
                return payload["items"]
            return payload

    async def fetch_products(self) -> list[dict[str, Any]]:
        return await self._fetch("products.json")

    async def fetch_stock(self) -> list[dict[str, Any]]:
        return await self._fetch("stocks.json")

    async def fetch_sales_documents(self) -> list[dict[str, Any]]:
        return await self._fetch("documents/sales.json")

    async def fetch_branches(self) -> list[dict[str, Any]]:
        return await self._fetch("offices.json")


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

    url = config.base_url.rstrip("/") + "/company.json"
    headers = {"access_token": config.api_key}

    try:
        with httpx.Client(timeout=timeout_s, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
    except httpx.HTTPError as exc:
        return False, f"No fue posible conectar a Bsale ({url}): {exc}", None

    if response.is_success:
        try:
            payload = response.json()
        except ValueError:
            payload = None
        return True, f"Conexion exitosa a {url}.", payload

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
