import logging
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.responses import RedirectResponse

from app.api.routes import router
from app.connectors.bsale import bsale_connector
from app.core.config import get_settings
from app.core.logging import configure_logging

logger = logging.getLogger(__name__)

_UI_FILE = Path(__file__).resolve().parent.parent / "static" / "index.html"


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    bsale_connector.reset()
    app = FastAPI(title="SotA Ingestion Service", version="0.1.0")

    # CORS — configurable via CORS_ORIGINS env var (comma-separated)
    cors_origins = getattr(settings, "cors_origins", None)
    if cors_origins:
        origins = [o.strip() for o in cors_origins.split(",") if o.strip()]
    else:
        origins = ["*"] if settings.app_env in ("local", "development") else []
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        t0 = time.monotonic()
        response = await call_next(request)
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        # Skip logging for static assets and UI routes
        if not request.url.path.startswith("/ui"):
            logger.info(
                "%s %s %d %dms",
                request.method,
                request.url.path,
                response.status_code,
                elapsed_ms,
            )
        return response

    app.include_router(router)

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/ui/overview", status_code=307)

    @app.get("/ui/{path:path}", include_in_schema=False)
    def ui_catchall(path: str = "") -> FileResponse:
        return FileResponse(
            _UI_FILE,
            headers={
                "Cache-Control": "no-store, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )

    @app.get("/ui", include_in_schema=False)
    def ui() -> RedirectResponse:
        return RedirectResponse(url="/ui/overview", status_code=307)

    return app


app = create_app()
