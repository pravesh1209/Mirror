"""NullProvider: always returns None. Routes every call to fallback."""
from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel

from ..base import ProviderHealth

T = TypeVar("T", bound=BaseModel)


class NullProvider:
    name = "null"

    async def complete_json(
        self,
        *,
        system: str,
        user: str,
        schema: type[T],
        timeout_s: float = 20.0,
    ) -> T | None:
        return None

    async def complete_text(
        self,
        *,
        system: str,
        user: str,
        timeout_s: float = 20.0,
    ) -> str | None:
        return None

    async def health(self) -> ProviderHealth:
        return ProviderHealth(name=self.name, available=False, last_error=None)


__all__ = ["NullProvider"]