"""Scenario routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..schemas import (
    ScenarioGenerateRequest,
    ScenarioGenerateResponse,
    ScenarioOut,
)
from ..services import scenarios as svc

router = APIRouter(tags=["scenarios"])


@router.post("/scenarios/generate", response_model=ScenarioGenerateResponse, status_code=201)
async def generate(
    payload: ScenarioGenerateRequest,
    db: AsyncSession = Depends(get_session),
) -> ScenarioGenerateResponse:
    sc = await svc.generate_scenario(
        db,
        session_id=payload.session_id,
        domain=payload.domain,
        target_axes=payload.target_axes,
        difficulty=payload.difficulty,
        use_bank_only=payload.use_bank_only,
    )
    return ScenarioGenerateResponse(scenario=sc)


@router.get("/scenarios/bank")
async def bank(
    domain: str | None = Query(default=None),
    limit: int = Query(default=12, ge=1, le=50),
    db: AsyncSession = Depends(get_session),
) -> dict:
    rows = await svc.list_bank(db, domain=domain, limit=limit)
    return {"count": len(rows), "scenarios": rows}


@router.get("/scenarios/{scenario_id}", response_model=ScenarioOut)
async def get_one(
    scenario_id: str,
    db: AsyncSession = Depends(get_session),
) -> ScenarioOut:
    return await svc.get_scenario_out(db, scenario_id)