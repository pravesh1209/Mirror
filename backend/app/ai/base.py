"""AI provider interface."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


@dataclass
class ProviderHealth:
    name: str
    available: bool
    last_error: str | None = None


@runtime_checkable
class AIProvider(Protocol):
    """Any LLM implementation must satisfy this."""

    name: str

    async def complete_json(
        self,
        *,
        system: str,
        user: str,
        schema: type[T],
        timeout_s: float = 20.0,
    ) -> T | None:
        """Return a validated instance of `schema`, or None on any failure.

        Implementations must never raise. Returning None is how the caller
        knows to fall back to the deterministic path.
        """
        ...

    async def complete_text(
        self,
        *,
        system: str,
        user: str,
        timeout_s: float = 20.0,
    ) -> str | None:
        ...

    async def health(self) -> ProviderHealth:
        ...


__all__ = ["AIProvider", "ProviderHealth"]