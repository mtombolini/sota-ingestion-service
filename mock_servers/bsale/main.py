from fastapi import FastAPI, Header, HTTPException

from mock_servers.bsale.data import DOCUMENTS, OFFICES, PRODUCTS, STOCKS

app = FastAPI(title="Bsale Mock API", version="0.1.0")


def validate(access_token: str | None):
    if not access_token:
        raise HTTPException(status_code=401, detail="missing access_token")


@app.get("/v1/products.json")
def products(access_token: str | None = Header(default=None, convert_underscores=False)):
    validate(access_token)
    return {"items": PRODUCTS, "count": len(PRODUCTS)}


@app.get("/v1/stocks.json")
def stocks(access_token: str | None = Header(default=None, convert_underscores=False)):
    validate(access_token)
    return {"items": STOCKS, "count": len(STOCKS)}


@app.get("/v1/offices.json")
def offices(access_token: str | None = Header(default=None, convert_underscores=False)):
    validate(access_token)
    return {"items": OFFICES, "count": len(OFFICES)}


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


@app.get("/health")
def health():
    return {"status": "ok", "service": "mock-bsale-api"}
