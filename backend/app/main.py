"""MIRROR FastAPI application entrypoint."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException as FastAPIHTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import __version__
from .api import blind_spots as blind_spots_api
from .api import decisions as decisions_api
from .api import demo as demo_api
from .api import events as events_api
from .api import health as health_api
from .api import model as model_api
from .api import predictions as predictions_api
from .api import profile as profile_api
from .api import scenarios as scenarios_api
from .api import sessions as sessions_api
from .config import settings
from .db import init_models

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
)
log = logging.getLogger("mirror")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info(
        "MIRROR backend starting (provider=%s, ai_available=%s)",
        settings.ai_provider,
        settings.ai_available,
    )
    await init_models()
    log.info("Database schema ensured")
    yield
    log.info("MIRROR backend shutting down")


app = FastAPI(
    title="MIRROR",
    description="AI Digital Twin of Decision Behavior",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    import uuid
    rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
    request.state.request_id = rid
    try:
        response = await call_next(request)
    except Exception:
        log.exception("Unhandled error request_id=%s path=%s", rid, request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL",
                    "message": "An unexpected error occurred.",
                    "details": None,
                    "request_id": rid,
                }
            },
        )
    response.headers["x-request-id"] = rid
    return response


@app.exception_handler(FastAPIHTTPException)
async def http_exception_handler(request: Request, exc: FastAPIHTTPException):
    rid = getattr(request.state, "request_id", None)
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail and "message" in detail:
        body = {"error": {**detail, "request_id": rid}}
    else:
        body = {
            "error": {
                "code": "HTTP_ERROR",
                "message": str(detail),
                "details": None,
                "request_id": rid,
            }
        }
    return JSONResponse(status_code=exc.status_code, content=body)


# --- routers ---
app.include_router(health_api.router, prefix="/api")
app.include_router(sessions_api.router, prefix="/api")
app.include_router(scenarios_api.router, prefix="/api")
app.include_router(events_api.router, prefix="/api")
app.include_router(decisions_api.router, prefix="/api")
app.include_router(profile_api.router, prefix="/api")
app.include_router(predictions_api.router, prefix="/api")
app.include_router(blind_spots_api.router, prefix="/api")
app.include_router(model_api.router, prefix="/api")
app.include_router(demo_api.router, prefix="/api")