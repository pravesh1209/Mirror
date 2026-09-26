"""Session + user lifecycle."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models import Session as SessionModel
from ..models import User


async def create_session(
    db: AsyncSession,
    *,
    display_name: str | None,
    mode: str,
) -> tuple[User, SessionModel]:
    user = User(display_name=display_name, is_demo=(mode == "demo"))
    db.add(user)
    await db.flush()

    sess = SessionModel(
        user_id=user.id,
        mode=mode,
        ai_provider=settings.ai_provider,
    )
    db.add(sess)
    await db.flush()
    return user, sess


async def end_session(db: AsyncSession, session_id: str) -> SessionModel | None:
    from ..db import utcnow
    sess = await db.get(SessionModel, session_id)
    if sess is None:
        return None
    sess.ended_at = utcnow()
    await db.flush()
    return sess


__all__ = ["create_session", "end_session"]