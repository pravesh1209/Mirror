"""Decision submission routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..schemas import DecisionRequest, DecisionResponse
from ..services import decisions as svc

router = APIRouter(tags=["decisions"])


@router.post("/scenarios/{scenario_id}/decision", response_model=DecisionResponse)
async def submit(
    scenario_id: str,
    payload: DecisionRequest,
    db: AsyncSession = Depends(get_session),
) -> DecisionResponse:
    return await svc.submit_decision(db, scenario_id=scenario_id, req=payload)