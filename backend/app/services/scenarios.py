"""Scenario generation and persistence.

Bank first, LLM second. Any AI failure silently falls through to the bank,
so the demo never breaks.
"""
from __future__ import annotations

import json
import logging

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..ai.factory import get_provider
from ..ai.prompts import load_prompt
from ..ai.schemas import GeneratedScenario
from ..models import Scenario, ScenarioOption
from ..models import Session as SessionModel
from ..schemas import (
    OptionAttributes,
    OptionOut,
    ScenarioAttributes,
    ScenarioOut,
)
from ..simulation import fallback_bank as bank

log = logging.getLogger("mirror.services.scenarios")


async def _used_seed_titles(db: AsyncSession, user_id: str) -> set[str]:
    q = await db.execute(
        select(Scenario.title).where(
            Scenario.user_id == user_id,
            Scenario.source == "seed",
        )
    )
    return set(q.scalars().all())


def scenario_to_out(sc: Scenario, opts: list[ScenarioOption]) -> ScenarioOut:
    return ScenarioOut(
        id=sc.id,
        domain=sc.domain,
        title=sc.title,
        body=sc.body,
        attributes=ScenarioAttributes(
            difficulty=sc.difficulty,
            risk=sc.risk,
            uncertainty=sc.uncertainty,
            time_pressure=sc.time_pressure,
            novelty=sc.novelty,
            reward=sc.reward,
            information_availability=sc.information_availability,
        ),
        time_limit_sec=sc.time_limit_sec,
        has_reveal=sc.has_reveal,
        reveal_payload=sc.reveal_payload,
        source=sc.source,
        options=[
            OptionOut(
                id=o.id,
                label=o.label,
                title=o.title,
                description=o.description,
                attributes=OptionAttributes(
                    risk=o.risk,
                    time_cost=o.time_cost,
                    money_cost=o.money_cost,
                    novelty=o.novelty,
                    uncertainty=o.uncertainty,
                    info_availability=o.info_availability,
                    reward=o.reward,
                ),
                is_novel=o.is_novel,
                display_order=o.display_order,
            )
            for o in opts
        ],
    )


async def _load_bundle(db: AsyncSession, scenario_id: str) -> tuple[Scenario | None, list[ScenarioOption]]:
    sc = await db.get(Scenario, scenario_id)
    if sc is None:
        return None, []
    q = await db.execute(
        select(ScenarioOption)
        .where(ScenarioOption.scenario_id == scenario_id)
        .order_by(ScenarioOption.display_order)
    )
    return sc, list(q.scalars().all())


async def get_scenario_out(db: AsyncSession, scenario_id: str) -> ScenarioOut:
    sc, opts = await _load_bundle(db, scenario_id)
    if sc is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": f"scenario {scenario_id} not found"},
        )
    return scenario_to_out(sc, opts)


async def _persist_generated(
    db: AsyncSession,
    *,
    sess: SessionModel,
    gen: GeneratedScenario,
    source: str,
) -> Scenario:
    sc = Scenario(
        user_id=sess.user_id,
        session_id=sess.id,
        domain=gen.domain,
        title=gen.title,
        body=gen.body,
        difficulty=gen.difficulty,
        risk=gen.risk,
        uncertainty=gen.uncertainty,
        time_pressure=gen.time_pressure,
        novelty=gen.novelty,
        reward=gen.reward,
        information_availability=gen.information_availability,
        time_limit_sec=gen.time_limit_sec,
        has_reveal=gen.has_reveal,
        reveal_payload=gen.reveal_payload,
        source=source,
    )
    db.add(sc)
    await db.flush()

    for i, o in enumerate(gen.options):
        db.add(
            ScenarioOption(
                scenario_id=sc.id,
                label=o.label,
                title=o.title,
                description=o.description,
                risk=o.risk,
                time_cost=o.time_cost,
                money_cost=o.money_cost,
                novelty=o.novelty,
                uncertainty=o.uncertainty,
                info_availability=o.info_availability,
                reward=o.reward,
                is_novel=o.is_novel,
                display_order=i,
            )
        )
    await db.flush()
    return sc


async def _try_llm(
    *,
    domain: str | None,
    target_axes: list[str] | None,
    difficulty: float | None,
) -> GeneratedScenario | None:
    provider = get_provider()
    if provider.name == "null":
        return None
    user_payload = {
        "domain": domain or "everyday",
        "target_attributes": target_axes or [],
        "difficulty": difficulty if difficulty is not None else 0.55,
        "avoid_domains": [],
        "banned_titles": [],
    }
    try:
        gen = await provider.complete_json(
            system=load_prompt("scenario_generator"),
            user=json.dumps(user_payload),
            schema=GeneratedScenario,
            timeout_s=20.0,
        )
    except Exception:
        log.exception("LLM scenario generation failed")
        return None
    return gen


def _bank_scenario(used_titles: set[str], domain: str | None) -> GeneratedScenario:
    pick = bank.pick_for_calibration(used_titles)
    if pick is None:
        # bank exhausted — pick by domain or random
        pool = bank.by_domain(domain)
        pick = pool[0]
    return GeneratedScenario.model_validate(pick)


async def generate_scenario(
    db: AsyncSession,
    *,
    session_id: str,
    domain: str | None = None,
    target_axes: list[str] | None = None,
    difficulty: float | None = None,
    use_bank_only: bool = False,
) -> ScenarioOut:
    sess = await db.get(SessionModel, session_id)
    if sess is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": f"session {session_id} not found"},
        )

    used = await _used_seed_titles(db, sess.user_id)
    gen: GeneratedScenario | None = None
    source = "seed"

    if not use_bank_only:
        gen = await _try_llm(domain=domain, target_axes=target_axes, difficulty=difficulty)
        if gen is not None:
            source = "llm"

    if gen is None:
        if target_axes:
            bank_pick = bank.pick_targeting_axis(target_axes[0])
        else:
            bank_pick = bank.pick_for_calibration(used) or bank.by_domain(domain)[0]
        gen = GeneratedScenario.model_validate(bank_pick)
        source = "seed"

    sc = await _persist_generated(db, sess=sess, gen=gen, source=source)
    sc_out = await get_scenario_out(db, sc.id)
    return sc_out


async def list_bank(db: AsyncSession, *, domain: str | None = None, limit: int = 12) -> list[dict]:
    rows = bank.by_domain(domain)[:limit]
    return rows


__all__ = [
    "generate_scenario",
    "get_scenario_out",
    "scenario_to_out",
    "list_bank",
]