"""Demo mode routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..db import get_session
from ..schemas import AIStatus
from ..services.demo import seed_demo, reset_demo

router = APIRouter(tags=["demo"])


@router.post("/demo/seed", status_code=201)
async def seed(db: AsyncSession = Depends(get_session)) -> dict:
    result = await seed_demo(db)
    return {
        "status": "seeded",
        "label": "DEMO DATA",
        "user_id": result["user_id"],
        "session_id": result["session_id"],
        "decisions": result["decisions"],
        "predictions": len(result["predictions"]),
        "ai_status": AIStatus(
            provider=settings.ai_provider,
            available=settings.ai_available,
            last_error=None,
        ).model_dump(),
    }


@router.post("/demo/reset")
async def reset(db: AsyncSession = Depends(get_session)) -> dict:
    deleted = await reset_demo(db)
    return {"status": "reset", "users_deleted": deleted}