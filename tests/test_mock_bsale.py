from fastapi.testclient import TestClient

from mock_servers.bsale.main import app


def test_mock_products_contract():
    client = TestClient(app)
    resp = client.get('/v1/products.json', headers={"access_token": "x"})
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body and "count" in body
    assert isinstance(body["items"], list)
