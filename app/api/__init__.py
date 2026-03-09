from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.responses import RedirectResponse

from app.api.routes import router
from app.connectors.bsale import bsale_connector
from app.core.logging import configure_logging

_UI_FILE = Path(__file__).resolve().parent.parent / "static" / "index.html"



def create_app() -> FastAPI:
    configure_logging()
    bsale_connector.reset()
    app = FastAPI(title="SotA Ingestion Service", version="0.1.0")
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
