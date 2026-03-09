from fastapi import FastAPI, Header, HTTPException

from mock_servers.bsale.data import (
    CLIENT_ADDRESSES,
    CLIENT_ATTRIBUTES,
    CLIENT_CONTACTS,
    CLIENTS,
    COMPANY,
    DOCUMENT_TYPES,
    DOCUMENTS,
    OFFICES,
    PRODUCTS,
    PRODUCT_TAXES,
    PRODUCT_VARIANTS,
    STOCKS,
)

app = FastAPI(title="Bsale Mock API", version="0.1.0")


def validate(access_token: str | None):
    if not access_token:
        raise HTTPException(status_code=401, detail="missing access_token")


def page_items(items: list[dict], *, limit: int = 25, offset: int = 0) -> dict:
    sliced = items[offset:offset + limit]
    return {"items": sliced, "count": len(items), "limit": limit, "offset": offset}


def find_client_or_404(client_id: int) -> dict:
    item = next((client for client in CLIENTS if client["id"] == client_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="client not found")
    return item


def find_office_or_404(office_id: int) -> dict:
    item = next((office for office in OFFICES if office["id"] == office_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="office not found")
    return item


def find_document_type_or_404(document_type_id: int) -> dict:
    item = next((document_type for document_type in DOCUMENT_TYPES if document_type["id"] == document_type_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="document type not found")
    return item


@app.get("/v1/products.json")
def products(
    access_token: str | None = Header(default=None, convert_underscores=False),
    limit: int = 25,
    offset: int = 0,
    state: int | None = None,
    classification: int | None = None,
):
    validate(access_token)
    items = PRODUCTS
    if state is not None:
        items = [product for product in items if int(product.get("state", 0)) == state]
    if classification is not None:
        items = [product for product in items if int(product.get("classification", 0)) == classification]
    return page_items(items, limit=limit, offset=offset)


@app.get("/v1/products/{product_id}.json")
def product(product_id: int, access_token: str | None = Header(default=None, convert_underscores=False)):
    validate(access_token)
    item = next((product for product in PRODUCTS if product["id"] == product_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="product not found")
    return item


@app.get("/v1/products/{product_id}/variants.json")
def product_variants(
    product_id: int,
    access_token: str | None = Header(default=None, convert_underscores=False),
    limit: int = 25,
    offset: int = 0,
):
    validate(access_token)
    items = PRODUCT_VARIANTS.get(product_id, [])
    return page_items(items, limit=limit, offset=offset)


@app.get("/v1/products/{product_id}/product_taxes.json")
def product_taxes(
    product_id: int,
    access_token: str | None = Header(default=None, convert_underscores=False),
    limit: int = 25,
    offset: int = 0,
):
    validate(access_token)
    items = PRODUCT_TAXES.get(product_id, [])
    return page_items(items, limit=limit, offset=offset)


@app.get("/v1/products/count.json")
def products_count(access_token: str | None = Header(default=None, convert_underscores=False)):
    validate(access_token)
    return {"count": len(PRODUCTS)}


@app.get("/v1/clients.json")
def clients(
    access_token: str | None = Header(default=None, convert_underscores=False),
    limit: int = 25,
    offset: int = 0,
    state: int | None = None,
    code: str | None = None,
):
    validate(access_token)
    items = CLIENTS
    if state is not None:
        items = [client for client in items if int(client.get("state", 0)) == state]
    if code is not None:
        items = [client for client in items if client.get("code") == code]
    return page_items(items, limit=limit, offset=offset)


@app.get("/v1/clients/count.json")
def clients_count(access_token: str | None = Header(default=None, convert_underscores=False)):
    validate(access_token)
    return {"count": len(CLIENTS)}


@app.get("/v1/clients/{client_id}.json")
def client(client_id: int, access_token: str | None = Header(default=None, convert_underscores=False)):
    validate(access_token)
    return find_client_or_404(client_id)


@app.get("/v1/clients/{client_id}/contacts.json")
def client_contacts(
    client_id: int,
    access_token: str | None = Header(default=None, convert_underscores=False),
    limit: int = 25,
    offset: int = 0,
):
    validate(access_token)
    find_client_or_404(client_id)
    return page_items(CLIENT_CONTACTS.get(client_id, []), limit=limit, offset=offset)


@app.get("/v1/clients/{client_id}/addresses.json")
def client_addresses(
    client_id: int,
    access_token: str | None = Header(default=None, convert_underscores=False),
    limit: int = 25,
    offset: int = 0,
    state: int | None = None,
):
    validate(access_token)
    find_client_or_404(client_id)
    items = CLIENT_ADDRESSES.get(client_id, [])
    if state is not None:
        items = [address for address in items if int(address.get("state", 0)) == state]
    return page_items(items, limit=limit, offset=offset)


@app.get("/v1/clients/{client_id}/attributes.json")
def client_attributes(
    client_id: int,
    access_token: str | None = Header(default=None, convert_underscores=False),
    limit: int = 25,
    offset: int = 0,
):
    validate(access_token)
    find_client_or_404(client_id)
    return page_items(CLIENT_ATTRIBUTES.get(client_id, []), limit=limit, offset=offset)


@app.get("/v1/stocks.json")
def stocks(access_token: str | None = Header(default=None, convert_underscores=False)):
    validate(access_token)
    return {"items": STOCKS, "count": len(STOCKS)}


@app.get("/v1/offices.json")
def offices(
    access_token: str | None = Header(default=None, convert_underscores=False),
    limit: int = 25,
    offset: int = 0,
    state: int | None = None,
):
    validate(access_token)
    items = OFFICES
    if state is not None:
        items = [office for office in items if int(office.get("state", 0)) == state]
    return page_items(items, limit=limit, offset=offset)


@app.get("/v1/offices/{office_id}.json")
def office(office_id: int, access_token: str | None = Header(default=None, convert_underscores=False)):
    validate(access_token)
    return find_office_or_404(office_id)


@app.get("/v1/offices/count.json")
def offices_count(access_token: str | None = Header(default=None, convert_underscores=False)):
    validate(access_token)
    return {"count": len(OFFICES)}


@app.get("/v1/document_types.json")
def document_types(
    access_token: str | None = Header(default=None, convert_underscores=False),
    limit: int = 25,
    offset: int = 0,
    state: int | None = None,
    codesii: str | None = None,
):
    validate(access_token)
    items = DOCUMENT_TYPES
    if state is not None:
        items = [document_type for document_type in items if int(document_type.get("state", 0)) == state]
    if codesii is not None:
        items = [document_type for document_type in items if document_type.get("codeSii") == codesii]
    return page_items(items, limit=limit, offset=offset)


@app.get("/v1/document_types/{document_type_id}.json")
def document_type(document_type_id: int, access_token: str | None = Header(default=None, convert_underscores=False)):
    validate(access_token)
    return find_document_type_or_404(document_type_id)


@app.get("/v1/document_types/count.json")
def document_types_count(access_token: str | None = Header(default=None, convert_underscores=False)):
    validate(access_token)
    return {"count": len(DOCUMENT_TYPES)}


@app.get("/v1/documents.json")
def documents(
    access_token: str | None = Header(default=None, convert_underscores=False),
    expand: str | None = None,
    state: str | None = None,
    limit: int = 25,
    offset: int = 0,
    documenttypeid: str | None = None,
):
    validate(access_token)
    result = DOCUMENTS
    if state is not None:
        result = [d for d in result if str(d.get("state", 0)) == state]
    if documenttypeid is not None:
        result = [d for d in result if d.get("document_type", {}).get("id") == documenttypeid]
    page = result[offset:offset + limit]
    return {"items": page, "count": len(result)}


@app.get("/v1/company.json")
def company(access_token: str | None = Header(default=None, convert_underscores=False)):
    validate(access_token)
    return COMPANY


@app.get("/health")
def health():
    return {"status": "ok", "service": "mock-bsale-api"}
