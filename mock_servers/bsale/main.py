from fastapi import FastAPI, Header, HTTPException

from mock_servers.bsale.data import OFFICES, PRODUCTS, SALES, STOCKS

app = FastAPI(title="Bsale Mock API", version="0.1.0")


def validate(access_token: str | None):
    if not access_token:
        raise HTTPException(status_code=401, detail="missing access_token")


@app.get("/v1/products.json")
def products(access_token: str | None = Header(default=None)):
    validate(access_token)
    return {"items": PRODUCTS, "count": len(PRODUCTS)}


@app.get("/v1/stocks.json")
def stocks(access_token: str | None = Header(default=None)):
    validate(access_token)
    return {"items": STOCKS, "count": len(STOCKS)}


@app.get("/v1/offices.json")
def offices(access_token: str | None = Header(default=None)):
    validate(access_token)
    return {"items": OFFICES, "count": len(OFFICES)}


@app.get("/v1/documents/sales.json")
def sales(access_token: str | None = Header(default=None)):
    validate(access_token)
    return {"items": SALES, "count": len(SALES)}


@app.get("/health")
def health():
    return {"status": "ok", "service": "mock-bsale-api"}
