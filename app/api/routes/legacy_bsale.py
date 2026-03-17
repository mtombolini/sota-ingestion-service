"""Legacy Bsale connector endpoints (direct connector state management)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.connectors.base import ConnectorConfigurationError, ConnectorMode
from app.connectors.bsale import bsale_connector

router = APIRouter(prefix="/connectors", tags=["connectors"])


class BsaleUpdateRequest(BaseModel):
    mode: ConnectorMode = Field(description="mock o real")
    base_url: str | None = Field(default=None, description="URL base a usar con este modo")
    api_key: str | None = Field(default=None, description="Token Bsale para modo real")
    check_connection: bool = Field(default=True, description="Si true, intenta conectar tras actualizar")


class BsaleStatusResponse(BaseModel):
    connector: str
    mode: ConnectorMode
    base_url: str
    api_key: str | None
    connected: bool | None = None
    message: str | None = None


def _bsale_masked_api_key() -> str | None:
    config = bsale_connector.config
    return config.masked_api_key() if config.mode == ConnectorMode.REAL else None


@router.get("/bsale", response_model=BsaleStatusResponse)
def get_bsale_status() -> BsaleStatusResponse:
    config = bsale_connector.config
    return BsaleStatusResponse(
        connector=config.name,
        mode=config.mode,
        base_url=config.base_url,
        api_key=_bsale_masked_api_key(),
        message="Conector configurado.",
    )


@router.patch("/bsale", response_model=BsaleStatusResponse)
def update_bsale(payload: BsaleUpdateRequest) -> BsaleStatusResponse:
    try:
        config = bsale_connector.update(mode=payload.mode, base_url=payload.base_url, api_key=payload.api_key)
    except ConnectorConfigurationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    connected = None
    message = "Configuracion guardada."
    if payload.check_connection:
        connected, message = bsale_connector.attempt_connection()

    return BsaleStatusResponse(
        connector=config.name,
        mode=config.mode,
        base_url=config.base_url,
        api_key=_bsale_masked_api_key(),
        connected=connected,
        message=message,
    )
