"""Prediction routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..schemas import (
    PredictionRequest,
    PredictionResponse,
    ResolveRequest,
    ResolveResponse,
    WhatIfRequest,
    WhatIfResponse,
)
from ..services import predictions as svc

router = APIRouter(tags=["predictions"])


@router.post("/predictions", response_model=PredictionResponse, status_code=201)
async def create(
    payload: PredictionRequest,
    db: AsyncSession = Depends(get_session),
) -> PredictionResponse:
    return await svc.create_prediction(db, payload)


@router.get("/predictions/{prediction_id}", response_model=PredictionResponse)
async def get_one(
    prediction_id: str,
    db: AsyncSession = Depends(get_session),
) -> PredictionResponse:
    return await svc.get_prediction(db, prediction_id)


@router.post("/predictions/{prediction_id}/resolve", response_model=ResolveResponse)
async def resolve(
    prediction_id: str,
    payload: ResolveRequest,
    db: AsyncSession = Depends(get_session),
) -> ResolveResponse:
    return await svc.resolve_prediction(
        db, prediction_id=prediction_id, decision_id=payload.decision_id
    )


@router.post("/predictions/{prediction_id}/whatif", response_model=WhatIfResponse)
async def whatif(
    prediction_id: str,
    payload: WhatIfRequest,
    db: AsyncSession = Depends(get_session),
) -> WhatIfResponse:
    return await svc.whatif_prediction(
        db, prediction_id=prediction_id, overrides=payload.overrides
    )