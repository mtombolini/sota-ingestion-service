from fastapi.testclient import TestClient

from mock_servers.bsale.main import app


def test_mock_products_contract():
    client = TestClient(app)
    resp = client.get('/v1/products.json?limit=1&offset=0', headers={"access_token": "x"})
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body and "count" in body and body["limit"] == 1
    assert isinstance(body["items"], list)
    assert len(body["items"]) == 1
    assert "product_taxes" in body["items"][0]


def test_mock_product_related_endpoints_contract():
    client = TestClient(app)

    variants = client.get('/v1/products/101/variants.json', headers={"access_token": "x"})
    taxes = client.get('/v1/products/101/product_taxes.json', headers={"access_token": "x"})

    assert variants.status_code == 200
    assert taxes.status_code == 200
    assert variants.json()["items"][0]["product"]["id"] == "101"
    assert taxes.json()["items"][0]["tax"]["id"] == "1"


def test_mock_clients_contract():
    client = TestClient(app)

    clients = client.get('/v1/clients.json?limit=1&offset=0', headers={"access_token": "x"})
    detail = client.get('/v1/clients/3001.json', headers={"access_token": "x"})
    contacts = client.get('/v1/clients/3001/contacts.json', headers={"access_token": "x"})
    addresses = client.get('/v1/clients/3001/addresses.json', headers={"access_token": "x"})
    attributes = client.get('/v1/clients/3001/attributes.json', headers={"access_token": "x"})

    assert clients.status_code == 200
    assert detail.status_code == 200
    assert contacts.status_code == 200
    assert addresses.status_code == 200
    assert attributes.status_code == 200
    assert clients.json()["count"] >= 1
    assert detail.json()["id"] == 3001
    assert contacts.json()["items"][0]["email"] == "pedro@donpedro.cl"
    assert addresses.json()["items"][0]["addressName"] == "Casa matriz"
    assert attributes.json()["items"][0]["name"] == "Segmento"


def test_mock_offices_contract():
    client = TestClient(app)

    offices = client.get('/v1/offices.json?limit=1&offset=0', headers={"access_token": "x"})
    detail = client.get('/v1/offices/1.json', headers={"access_token": "x"})
    count = client.get('/v1/offices/count.json', headers={"access_token": "x"})

    assert offices.status_code == 200
    assert detail.status_code == 200
    assert count.status_code == 200
    assert offices.json()["items"][0]["name"] == "Casa Matriz Santiago"
    assert detail.json()["municipality"] == "Providencia"
    assert count.json()["count"] >= 1


def test_mock_document_types_contract():
    client = TestClient(app)

    document_types = client.get('/v1/document_types.json?limit=1&offset=0', headers={"access_token": "x"})
    detail = client.get('/v1/document_types/2.json', headers={"access_token": "x"})
    count = client.get('/v1/document_types/count.json', headers={"access_token": "x"})

    assert document_types.status_code == 200
    assert detail.status_code == 200
    assert count.status_code == 200
    assert document_types.json()["items"][0]["id"] == 1
    assert detail.json()["codeSii"] == "33"
    assert count.json()["count"] >= 1
