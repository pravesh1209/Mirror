"""Model timeline routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..models import ModelUpdate, User
from ..schemas import TimelineEntry, TimelineResponse

router = APIRouter(tags=["model"])


@router.get("/model/timeline", response_model=TimelineResponse)
async def timeline(
    user_id: str = Query(...),
    db: AsyncSession = Depends(get_session),
) -> TimelineResponse:
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "user not found"})

    q = await db.execute(
        select(ModelUpdate)
        .where(ModelUpdate.user_id == user_id)
        .order_by(ModelUpdate.to_version.asc())
    )
    rows = list(q.scalars().all())

    entries: list[TimelineEntry] = []
    for r in rows:
        deltas = {
            k: float(v["after"])
            for k, v in (r.feature_deltas or {}).items()
            if isinstance(v, dict) and "after" in v
        }
        entries.append(
            TimelineEntry(
                version=r.to_version,
                at=r.created_at,
                after_decision_n=r.to_version,  # version increments 1:1 with decisions here
                kind=r.kind,
                narrative=r.narrative or "",
                deltas=deltas,
            )
        )

    return TimelineResponse(entries=entries)