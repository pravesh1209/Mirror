"""Event ingest routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..schemas import EventsBatchRequest, EventsBatchResponse
from ..services import decisions as svc

router = APIRouter(tags=["events"])


@router.post(
    "/scenarios/{scenario_id}/events",
    response_model=EventsBatchResponse,
    status_code=202,
)
async def ingest(
    scenario_id: str,
    payload: EventsBatchRequest,
    db: AsyncSession = Depends(get_session),
) -> EventsBatchResponse:
    return await svc.ingest_events(db, scenario_id=scenario_id, req=payload)