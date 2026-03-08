from fastapi.testclient import TestClient

from app.api import create_app
from app.connectors.base import ConnectorMode
from app.providers import provider_registry


def test_provider_registry_exposes_bsale() -> None:
    provider = provider_registry.get("bsale")

    assert provider.display_name == "Bsale"
    assert provider.default_base_url(mode=ConnectorMode.MOCK).endswith("/v1")
    assert provider.supports_job("sync_product_catalog")


def test_admin_providers_endpoint_exposes_provider_defaults() -> None:
    client = TestClient(create_app())

    response = client.get("/admin/providers")

    assert response.status_code == 200
    payload = response.json()
    bsale = next(item for item in payload if item["key"] == "bsale")
    assert bsale["default_base_urls"]["mock"].endswith("/v1")
    assert bsale["default_base_urls"]["real"].startswith("https://")
    assert any(job["job_type"] == "sync_product_catalog" for job in bsale["jobs"])
