"""FastAPI application factory."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import __version__
from app.config import REPO_ROOT, Settings, get_settings
from app.routers import chat, extract, predict
from app.services.models import warm_cache

log = logging.getLogger(__name__)


def _problem(status: int, title: str, detail: str, **extra: Any) -> JSONResponse:
    """RFC 7807-shaped error body, so the client has one error contract."""
    return JSONResponse(
        status_code=status,
        content={"status": status, "title": title, "detail": detail, **extra},
    )


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Load every estimator before the first request rather than during it.

    Unpickling a 300-tree forest is tens of milliseconds, and the prototype
    paid that on every single prediction. Doing it here also surfaces a missing
    or corrupt model file in the startup log instead of in a user's response.
    """
    status = warm_cache()
    ready = sorted(slug for slug, ok in status.items() if ok)
    missing = sorted(slug for slug, ok in status.items() if not ok)
    log.info("Models ready (%d): %s", len(ready), ", ".join(ready) or "none")
    if missing:
        log.warning("Models unavailable (%d): %s", len(missing), ", ".join(missing))
    yield


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    app = FastAPI(
        title="MDPS API",
        version=__version__,
        summary="Clinical screening, lab-report analysis, and report history for the MDPS client.",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        lifespan=_lifespan,
    )

    # Dev traffic is same-origin through the Vite proxy, so CORS matters only
    # for deployments that split the two origins.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        # The screening router raises 422 with a list of {field, message} so it
        # can report every bad field at once. Routing that through the same
        # `errors` key as FastAPI's own validation errors means the client has
        # one error shape to handle, not two.
        if isinstance(exc.detail, list):
            return _problem(
                exc.status_code,
                "Validation failed",
                "One or more fields are invalid.",
                errors=exc.detail,
            )
        return _problem(exc.status_code, "Request failed", str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return _problem(
            422,
            "Validation failed",
            "One or more fields are invalid.",
            errors=[
                {"field": ".".join(str(p) for p in e["loc"][1:]), "message": e["msg"]}
                for e in exc.errors()
            ],
        )

    @app.get("/api/health", tags=["meta"])
    async def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "version": __version__,
            "environment": settings.environment,
            "ai_enabled": settings.has_groq,
        }

    app.include_router(predict.router)
    # Report ingestion. Additive: it turns documents into numbers and never
    # touches the estimators, so scoring behaviour is unchanged.
    app.include_router(extract.router)
    # VERA. Conversational only — it never produces a risk score.
    app.include_router(chat.router)

    from fastapi.staticfiles import StaticFiles
    web_dir = REPO_ROOT / "vitals-web"
    if web_dir.exists():
        app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="static")

    return app


app = create_app()
