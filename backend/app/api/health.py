"""Health & status endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .. import __version__
from ..config import settings
from ..db import get_session
from ..schemas import AIStatus, HealthResponse, StatusResponse

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", version=__version__)


@router.get("/status", response_model=StatusResponse)
async def status(session: AsyncSession = Depends(get_session)) -> StatusResponse:
    db_state = "ok"
    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover (only hit on broken db)
        db_state = f"error: {type(exc).__name__}"

    ai = AIStatus(
        provider=settings.ai_provider,
        available=settings.ai_available,
        last_error=None,
    )
    mode = "live" if settings.ai_available else "fallback"
    return StatusResponse(db=db_state, ai=ai, mode=mode)
