"""Session routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..db import get_session
from ..models import Session as SessionModel
from ..schemas import AIStatus, SessionCreate, SessionResponse
from ..services.sessions import create_session

router = APIRouter(tags=["sessions"])


def _ai_status() -> AIStatus:
    return AIStatus(
        provider=settings.ai_provider,
        available=settings.ai_available,
        last_error=None,
    )


@router.post("/sessions", response_model=SessionResponse, status_code=201)
async def create(
    payload: SessionCreate,
    db: AsyncSession = Depends(get_session),
) -> SessionResponse:
    user, sess = await create_session(db, display_name=payload.display_name, mode=payload.mode)
    return SessionResponse(
        session_id=sess.id,
        user_id=user.id,
        mode=sess.mode,
        ai_status=_ai_status(),
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get(
    session_id: str,
    db: AsyncSession = Depends(get_session),
) -> SessionResponse:
    sess = await db.get(SessionModel, session_id)
    if sess is None:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "session not found"})
    return SessionResponse(
        session_id=sess.id,
        user_id=sess.user_id,
        mode=sess.mode,
        ai_status=_ai_status(),
    )